from Common.utils import Utils
from Common.urls import URL

from Symbol.symbol_generator import SymbolGenerator

class OMS:
	def __init__(self, symbol, trade_logger, info_logger):
		self._default_order_type = 'market_order'
		self._symbol = symbol
		self._trade_logger = trade_logger
		self._info_logger = info_logger

	def log_trade(self, trade_details):
		self._trade_logger.info(trade_details)

	def place_order_live(self, pair, qty, side, price, stop_price, leverage=1.0, order_type="limit_order"):

		timestamp = Utils.get_timestamp()
		body = {
		  "side": side,
		  "order_type": order_type,
		  "market": pair,
		  "price": price,
		  "quantity": qty,
		  "ecode": 'B',
		  "leverage": leverage,
		  "trailing_sl" : True,
		  "trail_percent" : 2,
		  "stop_price" : stop_price,
		  "timestamp": timestamp
		}

		json_body, headers = Utils.generate_signature(body)
		url = URL.place_margin_order_url()
		response = Utils.post_request(url, json_body, headers)
		self._trade_logger.info(f"NEW ORDER : {response}")
		return response

	def cancel_order_live(self, uid):
		timestamp = Utils.get_timestamp()

		body = {
			"id" : uid,
			"timestamp" : timestamp
		}		

		json_body, headers = Utils.generate_signature(body)
		url = URL.get_cancel_order_url()
		response = Utils.post_request(url, json_body, headers)
		self._trade_logger.info(f"CANCEL ORDER : id : {uid} | {response}")
		return response

	def exit_order_live(self, uid):
		timestamp = Utils.get_timestamp()

		body = {
			"id" : uid,
			"timestamp" : timestamp
		}

		json_body, headers = Utils.generate_signature(body)
		url = URL.get_exit_order_url()
		response = Utils.post_request(url, json_body, headers)
		self._trade_logger.info(f"EXIT ORDER : id : {uid} | {response}")
		return response

	def place_order_paper(self, side, quantity, price):
		if quantity == 0:
			print('Insufficient funds!')
			return

		timestamp = Utils.get_timestamp()
		try:
			response = {"side" : side,
						"timestamp" : timestamp, 
						"id" : 0, 
						"fee_amount" : price * quantity * 0.001,
						"avg_entry" : price,
						"turnover" : price * quantity,
						"quantity" : quantity,
						"status" : "open"}
		except Exception as e:
			self._info_logger.error(e)
			return None
			
		self._trade_logger.info(response)
		return response