from Common.utils import Utils
from Common.urls import URL
from Common.order_side import OrderSide

from OMS.oms import OMS

from operator import itemgetter
from Symbol.symbol_generator import SymbolGenerator

import time
import Common.not_secret_info as secrets


class Execution:
	def __init__(self, symbol, resource_percent, oms, mode='Paper'):
		self._symbol = symbol
		self._resource_percent = resource_percent
		self._oms = oms
		self._mode = mode
		
		self._current_resource = self.update_current_monetary_resource()
		self._current_inventory = self.update_current_inventroy()

		if self._current_resource == None:
			raise Exception("ResrouceCollectionException")
		if self._current_inventory == None:
			raise Exception("InventoryCollectionException")

		self._active_buy_orders = self.get_active_orders('buy')
		self._active_sell_orders = self.get_active_orders('sell')

		if self._active_buy_orders == None or self._active_sell_orders == None:
			raise Exception("ActiveOrderCollectionException")
		
		if mode == 'Paper':
			self._current_inventory = 0

		self._total_turnover = 0
		self._current_net_pnl = 0
		self._round_trips = 0
		self._entry_price = 0

	def update_current_monetary_resource(self):
		return self.get_current_resource(secrets.BASE_CURR) * self._resource_percent * 0.01

	def update_current_inventroy(self):
		return self.get_current_resource(self._symbol._symbol_details['target_currency_short_name'])

	def get_current_resource(self, coin):
		timestamp = Utils.get_timestamp()
		body = {
			"timestamp" : timestamp
		}
		
		json_body, headers = Utils.generate_signature(body)
		url = URL.get_resource_url()
		resources = Utils.post_request(url, json_body, headers)
		#print(resources)
		try:
			available_resource = float([r['balance'] for r in resources if r['currency'] == coin][0])
		except:
			return None
		return available_resource

	def get_active_orders(self, side):
		symbol_name = self._symbol._symbol
		timestamp = Utils.get_timestamp()
		body = {
			"side" : side,
			"market" : symbol_name,
			"timestamp" : timestamp
		}

		json_body, headers = Utils.generate_signature(body)
		url = URL.get_active_order_url()
		active_orders = Utils.post_request(url, json_body, headers)

		return active_orders['orders']

	def set_quantity(self, price):
		if price == 0:
			raise Exception("InvalidPriceError")

		qty = (self._current_resource / price)
		min_qty = self._symbol._symbol_details['min_quantity']
		return int(qty / min_qty) * min_qty

	def update_trade(self, order_response):
		if order_response['status'] == False:
			print('Placing Order failed')
			return False

		if self._current_inventory == 0:
			self._entry_price = order_response['avg_price']

		if(self._mode == 'Paper'):
			if order_response['side'] == OrderSide.BUY:
				print(order_response['quantity'])
				self._current_inventory += order_response['quantity']
			elif order_response['side'] == OrderSide.SELL:
				self._current_inventory -= order_response['quantity']

			if self._current_inventory == 0:
				self._current_resource += order_response['turnover'] - order_response['fee_amount']
				if order_response['side'] == OrderSide.BUY:
					self._current_net_pnl += (self._entry_price - order_response['avg_price']) * order_response['quantity'] - order_response['fee_amount']
				else:
					self._current_net_pnl += (order_response['avg_price'] - self._entry_price) * order_response['quantity'] - order_response['fee_amount']
			else:
				self._current_resource -= order_response['turnover'] + order_response['fee_amount']

			self._total_turnover += order_response['turnover']
		else:
			self._current_inventory = self.update_current_inventroy()
			if self._current_inventory == 0:
				self._current_resource = self.update_current_monetary_resource()
				self._current_net_pnl += (self._current_resource - previous_resource)
				self._round_trips += 1

			self._current_resource = self.update_current_monetary_resource()
			self._total_turnover += order_response['turnover']
		
		return True
	
	def set_action(self, signal, bid_price, ask_price, exit_flag_buy, exit_flag_sell):
		if self._current_inventory == 0: 
			if signal > 0:
				try:
					quantity = self.set_quantity(ask_price)
				except Exception as e:
					raise Exception("QuantitySettingException")
				
				side = OrderSide.BUY
				
				order_response = self._oms.place_order_paper(side, quantity, ask_price)
				if order_response == None:
					raise Exception("PlacingPaperOrderException")
				
				self.update_trade(order_response)
				
				print(f"Placing BUY ORDER for ENTRY | price : {ask_price} inv : {self._current_inventory} resources : {self._current_resource} pnl : {self._current_net_pnl} ")
				return True
			if signal < 0:
				try:
					quantity = self.set_quantity(bid_price)
				except Exception as e:
					raise Exception("QuantitySettingException")
				
				side = OrderSide.SELL
				
				order_response = self._oms.place_order_paper(side, quantity, bid_price)
				if order_response == None:
					raise Exception("PlacingPaperOrderException")

				self.update_trade(order_response)
				print(f"Placing SELL ORDER for ENTRY | price : {bid_price} inv : {self._current_inventory} resources : {self._current_resource} pnl : {self._current_net_pnl}")
				return
		if self._current_inventory > 0:
			if signal < 0:
				try:
					quantity = self._current_inventory
				except Exception as e:
					raise Exception("QuantitySettingException")
				
				side = OrderSide.SELL
				
				order_response = self._oms.place_order_paper(side, quantity, bid_price)
				if order_response == None:
					raise Exception("PlacingPaperOrderException")

				self.update_trade(order_response)
				print(f"Placing SELL ORDER for EXIT | price : {bid_price} inv : {self._current_inventory} resources : {self._current_resource} pnl : {self._current_net_pnl}")
				return
		if self._current_inventory < 0:
			if signal > 0:
				try:
					quantity = -1 * self._current_inventory
				except Exception as e:
					raise Exception("QuantitySettingException")
				
				side = OrderSide.BUY
				
				order_response = self._oms.place_order_paper(side, quantity, ask_price)
				if order_response == None:
					raise Exception("PlacingPaperOrderException")
				self.update_trade(order_response)
				print(f"Placing BUY ORDER for EXIT | price : {ask_price} inv : {self._current_inventory} resources : {self._current_resource} pnl : {self._current_net_pnl}")
				return