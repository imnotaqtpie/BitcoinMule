BASE_URL = 'https://api.coindcx.com'
DATA_URL = 'https://public.coindcx.com'

market_url = '/exchange/v1/markets'
market_details_url = '/exchange/v1/markets_details'

class URL:
	@staticmethod
	def get_market_url():
		return f"{BASE_URL}/exchange/v1/markets"

	@staticmethod
	def get_market_details_url():
		return f"{BASE_URL}/exchange/v1/markets_details"

	@staticmethod
	def get_candles_url():
		return f"{DATA_URL}/market_data/candles"

	@staticmethod
	def get_resource_url():
		return f"{BASE_URL}/exchange/v1/users/balances"

	@staticmethod
	def get_active_order_url():
		return f"{BASE_URL}/exchange/v1/orders/active_orders"

	@staticmethod
	def get_send_order_url():
		return f"{BASE_URL}/exchange/v1/orders/create"

	@staticmethod
	def get_ltp_url():
		return f"{BASE_URL}/exchange/ticker"