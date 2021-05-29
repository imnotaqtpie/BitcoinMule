from Common.utils import Utils
from Common.urls import URL

from Symbol.symbol_generator import SymbolGenerator

class OMS:
	def __init__(self, symbol, log_path):
		self._default_order_type = 'market_order'
		self._symbol = symbol
		self._logger = Utils.setup_logger(log_path)

	def place_order_live(self, side, quantity):
		if quantity == 0:
			print('Insufficient funds!')
			return

		market_name = self._symbol._symbol
		order_type = self._default_order_type
		timestamp = Utils.get_timestamp()

		body = {
			"side" : side,
			"order_type" : order_type,
			"total_quantity" : quantity,
			"timestamp" : timestamp
		}

		json_body, headers = Utils.generate_signature(body)
		url = URL.get_send_order_url()
		order_stats = Utils.post_request(url, json_body, headers)
		return True

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
					"avg_price" : price,
					"turnover" : price * quantity,
					"quantity" : quantity,
					"status" : "TRADE_CONFIRM"}
		except:
			return None
		self._logger.info(response)
		return response