from Common.utils import Utils
from Common.urls import URL
from Common.order_side import OrderSide

from OMS.oms import OMS

from operator import itemgetter
from Symbol.symbol_generator import SymbolGenerator

import time
import Common.not_secret_info as secrets


class Execution:
	def __init__(self, symbol, resource_percent, target, stop_loss, trail_loss, oms, mode='Paper'):
		self._symbol = symbol
		self._resource_percent = resource_percent
		self._target = target
		self._stop_loss = stop_loss
		self._trail_loss = trail_loss
		self._oms = oms
		self._mode = mode
		self._max_price = 0
		self._min_price = float("inf")
		self._entry_price = 0
		self._current_order_response = None
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
		return round(int(qty / min_qty) * min_qty, 4)

	def update_trade_paper(self):
		order_response = self._current_order_response
		if self._current_inventory == 0:
			self._entry_price = order_response['avg_entry']
	
		if order_response['side'] == OrderSide.BUY:
			self._current_inventory += order_response['quantity']
		elif order_response['side'] == OrderSide.SELL:
			self._current_inventory -= order_response['quantity']

		if self._current_inventory == 0:
			self._max_price = 0
			self._min_price = float("inf")
			self._current_resource += order_response['turnover'] - order_response['fee_amount']
			if order_response['side'] == OrderSide.BUY:
				self._current_net_pnl += (self._entry_price - order_response['avg_entry']) * order_response['quantity'] - order_response['fee_amount']
			else:
				self._current_net_pnl += (order_response['avg_entry'] - self._entry_price) * order_response['quantity'] - order_response['fee_amount']
			self._current_order_response = None
		else:
			self._current_resource -= order_response['turnover'] + order_response['fee_amount']

		self._total_turnover += order_response['turnover']
		return True

	def update_trade(self):
		order_response = self._current_order_response
		self._round_trips += 1
		self._current_net_pnl += order_response['pnl']
		self._current_resource = self.update_current_monetary_resource()
		self._total_turnover += (order_response['avg_entry'] + order_response['avg_exit']) / 2 * order_response['quantity'] + order_response['entry_fee'] + order_response['exit_fee']
		self._oms.log_trade(order_response)
		self._current_order_response = None
		self._max_price = 0
		self._min_price = float("inf")
		return True
	
	def set_exit_flag(self, price, signal):
		if self._current_order_response['side'] == OrderSide.BUY:
			if price > self._max_price:
				self._max_price = price
			if self._entry_price != 0:
				percent_change = (price - self._entry_price) * 100 / self._entry_price
				trail_percent = (price - self._max_price) * 100 / price

				if signal == -1:
					return True
				elif percent_change >= self._target:
					return True
				elif percent_change <= -1 * self._stop_loss:
					return True
				elif trail_percent <= -1* self._trail_loss:
					return True
			print(f"Open Buy : current_p {price} | signal : {signal} | entry {self._entry_price} | max price : {self._max_price} | resource : {self._current_resource} | total_pnl : {self._current_net_pnl}")

		if self._current_order_response['side'] == OrderSide.SELL:
			if price < self._min_price:
				self._min_price = price
			if self._entry_price != 0:
				percent_change = (self._entry_price - price) * 100 / self._entry_price
				trail_percent = (self._min_price - price) * 100 / price

				if signal == 1:
					return True
				if percent_change >= self._target:
					return True
				elif percent_change <= -1 * self._stop_loss:
					return True
				elif trail_percent <= -1 * self._trail_loss:
					return True
			print(f"Open Sell : current_p {price} | signal : {signal} | entry {self._entry_price} | min price : {self._min_price} | resource : {self._current_resource} | total_pnl : {self._current_net_pnl}")

		return False

	def check_order_status(self, uid=None):
		if uid == None and self._current_order_response == None:
			return
		if uid == None:
			uid = self._current_order_response['id']
		body = {
			"id" : uid,
			"timestamp" : Utils.get_timestamp() 
		}
		url = URL.get_order_status_url()
		json_body, headers = Utils.generate_signature(body)
		order_status = Utils.post_request(url, json_body, headers)
		self._current_order_response = order_status[0]

	def get_stop_price(self, price, side):
		if side == OrderSide.BUY:
			stop_price = price - (self._stop_loss * price) / 100
		elif side == OrderSide.SELL:
			stop_price = price + (self._stop_loss * price) / 100

		return round(stop_price, 5)

	def place_new_order(self, side, price, quantity):
		stop_price = self.get_stop_price(price, side)
		if self._mode == 'Paper':
			self._current_order_response = self._oms.place_order_paper(side, quantity, price)
			if self._current_order_response['status'] == 'open':
				self._entry_price = price
				self.update_trade_paper()

		elif self._mode == 'Live':
			self._current_order_response = self._oms.place_order_live(self._symbol._symbol, quantity, side, price, stop_price)[0]
			self._current_resource = self.update_current_monetary_resource()
			order_id = self._current_order_response['id']	

		if self._current_order_response == None:
			raise Exception("PlacingNewOrderException")

		return True

	def modify_order(self, uid, side, price, quantity):
		self.cancel_order(uid)
		self.place_new_order()

	def cancel_order(self):
		uid = self._current_order_response['id']
		can_response = self._oms.cancel_order_live(uid)
		time.sleep(1)
		self.check_order_status()
		if can_response['status'] == 200 and self._current_order_response['status'] == 'cancelled':
			self._current_order_response = None
			self._current_resource = self.update_current_monetary_resource()
			self._current_inventory = self.update_current_inventroy()
			return True
		else:
			return False

	def place_exit_order(self, price):
		if self._current_order_response == None:
			return True
		if self._mode == 'Paper':
			if self._current_order_response['side'] == OrderSide.BUY:
				side = OrderSide.SELL
			elif self._current_order_response['side'] == OrderSide.SELL:
				side = OrderSide.BUY
			quantity = float(self._current_order_response['quantity'])	
			self._current_order_response = self._oms.place_order_paper(side, quantity, price)
			self.update_trade_paper()

		elif self._mode == 'Live':
			uid = self._current_order_response['id']
			exit_response = self._oms.exit_order_live(uid)
			if exit_response['status'] == 200:
				self.check_order_status()
				if self._current_order_response['status'] == "close":
					self.update_trade()
					print("Exit successful! Exiting immediately")
					return True
				else:
					time.sleep(5)
					self.check_order_status()
					if self._current_order_response['status'] == "close":
						self.update_trade()
						print("Exiting after waiting!")
					else:
						return False
			else:
				return False

	def set_action(self, signal, bid_price, ask_price):
		exit_flag = False
		if self._mode == "Live":
			self.check_order_status()
		if self._current_order_response == None:
			if signal == 0:
				print(f"Signal Neutral! | price : {bid_price} | resource : {self._current_resource} | total_pnl : {self._current_net_pnl}")
				return True
			if signal > 0:
				price = bid_price
				side = OrderSide.BUY
			if signal < 0:
				price = ask_price
				side = OrderSide.SELL

			try:
				quantity = self.set_quantity(price)
			except Exception as e:
				raise Exception("QuantitySettingException")

			self.place_new_order(side, price, quantity)

			if self._current_order_response['status'] == 'init':
				self.check_order_status()

			print(f"Placed entry order || signal : {signal} | side : {side} | price : {price} | qty : {quantity} | pnl : {self._current_net_pnl} | inventory : {self._current_inventory}")
			return True
		else:
			if self._current_order_response['status'] == 'init':
				if signal > 0:
					price = bid_price
					side = OrderSide.BUY
				if signal < 0:
					price = ask_price
					side = OrderSide.SELL
				if signal == 0:
					print(f"Cancelling Order! Signal died before fill.")
					self.cancel_order()
					return True

				if self._current_order_response['price'] == price and self._current_order_response['side'] == side:
					return True
				self.cancel_order()

				try:
					quantity = self.set_quantity(price)
				except Exception as e:
					raise Exception("QuantitySettingException")
				self.place_new_order(side, price, quantity)
				if self._current_order_response['status'] == 'init':
					self.check_order_status()
				print(f"Modifying order || side : {side} | price : {price} | qty : {quantity} | pnl : {self._current_net_pnl} | inventory : {self._current_inventory}")
				return True

			if self._current_order_response['status'] == 'open':
				self._entry_price = self._current_order_response['avg_entry']
				if self._current_order_response['side'] == OrderSide.BUY:
					exit_flag = self.set_exit_flag(bid_price, signal)
				if self._current_order_response['side'] == OrderSide.SELL:
					exit_flag = self.set_exit_flag(ask_price, signal)

				if self._mode == 'Live':
					self._current_inventory = self.update_current_inventroy()
					self._current_resource = self.update_current_monetary_resource()
					
				if exit_flag == True:
					side = self._current_order_response['side']
					quantity = self._current_order_response['quantity']
					if side == OrderSide.BUY:
						price = ask_price
					elif side == OrderSide.SELL:
						price = bid_price
					self.place_exit_order(price)
					print(f"Placed exit order || side : {side} | price : {price} | qty : {quantity} | total_pnl : {self._current_net_pnl} | inventory : {self._current_inventory}")
					return True

"""
symbol_name = 'MATICUSDT'

trade_log_path = f"D:/CryptoBot/LOGS/log_file_{symbol_name}_{time.time()}_trade.log"
error_log_path = f"D:/CryptoBot/LOGS/log_file_{symbol_name}_{time.time()}_error.log"

error_logger = Utils.setup_logger(error_log_path)
trade_logger = Utils.setup_logger(trade_log_path)

sg = SymbolGenerator(symbol_name, error_logger)
oms = OMS(symbol_name, trade_logger, error_logger)
exe = Execution(sg, 50, 2,1,1.5,oms,"Paper")
signal = 1
bid_price = 1.70
ask_price = 1.71

exe.set_action(1, bid_price, ask_price)
exe.set_action(-1, 1.72, 1.72)
exe.set_action(-1, 1.94, 1.92)
exe.set_action(-1, 1.83, 1.83)
"""