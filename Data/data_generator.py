import requests
import time

import pandas as pd

from operator import itemgetter

from Common.utils import Utils
from Common.urls import URL 

class DataGenerator:
	def __init__(self, symbolgen):
		self._symbolGen = symbolgen
		self._data = None

	def get_symbol_data(self, interval, limit):
		query = {'pair' : self._symbolGen._symbol_details['pair'], 'interval' : interval, 'limit' : limit}
		url = URL.get_candles_url()
		
		data = Utils.process_requests(url, query)
		if data == None:
			raise Exception("DataFetchingException")

		open_ = list(map(itemgetter('open'), data))
		high_ = list(map(itemgetter('high'), data))
		low_ = list(map(itemgetter('low'), data))
		close_ = list(map(itemgetter('close'), data))
		vol_ = list(map(itemgetter('volume'), data))

		self._data = pd.DataFrame({  'open' : open_, 
						'high' : high_,
						'low' : low_,
						'close' : close_,
						'volume' : vol_})

	def get_ltp(self):
		url = URL.get_ltp_url()
		ltp = Utils.process_requests(url)
		try:
			data = [r for r in ltp if r['market'] == self._symbolGen._symbol][0]
			return data
		except Exception as e:
			return None
