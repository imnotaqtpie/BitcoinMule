import requests
import time
import math

import numpy as np
import pandas as pd

class SignalGenerator:
	def __init__(self):
		self._signal_ready = False
		self._current_signal = 0
		self._exit_flag_buy = False
		self._exit_flag_sell = False

	def get_bollinger_bands(self, data, w, sd_entry, sd_exit):
		arr = data['open']
		df = pd.Series(arr)
		ma = df.rolling(w).mean()
		msd = df.rolling(w).std()

		bollinger_high = ma + (msd * sd_entry)
		bollinger_low = ma - (msd * sd_entry)
		bollinger_high_high = ma + (msd * (sd_exit))
		bollinger_low_low = ma - (msd * (sd_entry))

		bollinger_high = list(bollinger_high.dropna().values)
		bollinger_low = list(bollinger_low.dropna().values)
		bollinger_high_high = list(bollinger_high_high.dropna().values)
		bollinger_low_low = list(bollinger_low_low.dropna().values)
		l = len(bollinger_high)

		for i in range(len(arr) - l):
			bollinger_high.insert(0,0)
			bollinger_low.insert(0,0)
			bollinger_high_high.insert(0,0)
			bollinger_low_low.insert(0,0)

		self._bollinger_high = bollinger_high
		self._bollinger_low = bollinger_low
		self._bollinger_high_high = bollinger_high_high
		self._bollinger_low_low = bollinger_low_low

		self._signal_ready = True

	def generate_signal(self, data, w, sd_entry, sd_exit, price):
		try:
			self.get_bollinger_bands(data, w, sd_entry, sd_exit)
		except Exception as e:
			raise e


		if price <= self._bollinger_low[-1]:
			self._current_signal = 1
		elif price >= self._bollinger_high[-1]:
			self._current_signal = -1
		else:
			self._current_signal = 0

		#if price <= self._bollinger_low_low[-1]:
		#	self._exit_flag_buy = True
		#elif price >= self._bollinger_high_high[-1]:
		#	self._exit_flag_sell = True