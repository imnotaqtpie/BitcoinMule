import sys
import requests

from Common.utils import Utils
from Common.urls import URL 

class SymbolGenerator:
	def __init__(self, symbol, logger):
		self._symbol = symbol
		self._symbol_details = self.get_symbol_details()
		self._logger = logger
		if self._symbol_details == None:
			raise Exception("SymbolGeneratorException")
		
	def validate_symbol(self):
		url = URL.get_market_url()
		market_names = Utils.process_requests(url)
		if self._symbol not in market_names:
			raise Exception("InvalidSymbolNameException")
		return True

	def update_symbols(self, symbol):
		self._symbol = symbol

	def get_symbol_details(self):
		try:
			self.validate_symbol()
		except Exception as e:
			self._logger.error(e)
			return None
			
		url = URL.get_market_details_url()
		market_details = Utils.process_requests(url)

		try:
			details = list(filter(lambda x : x["coindcx_name"] == self._symbol, market_details))[0]
		except Exception as e:
			self._logger.error(f"FetchingMarketDetailsException : {e}")
			return None	

		return details
