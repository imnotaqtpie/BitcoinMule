import requests
import time
import math

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from Common.utils import Utils

from Symbol.symbol_generator import SymbolGenerator

from Data.data_generator import DataGenerator

from Indicators.macd import MACD
from Indicators.bollinger import BollingerBands
from Indicators.super_trend import SuperTrend 
from Indicators.ema import EMA

class SignalGenerator:
	def __init__(self):
		self._signal_ready = False
		self._current_signal = 0
		self._exit_flag_buy = False
		self._exit_flag_sell = False

	def generate_signal(self, data, mode, price, signal_stats):
		#Use the Indicator class and get variable objects
		if mode == 'BOLLINGER':
			try:
				signals = BollingerBands.get_bollinger_bands(data, signal_stats['w'], signal_stats['sd'])
			except Exception as e:
				raise e
			if price <= signals['bollinger_low'][-1]:
				self._current_signal = -1
			elif price >= signals['bollinger_high'][-1]:
				self._current_signal = 1
			else:
				self._current_signal = 0

		elif mode == 'MACD':
			try:
				signals = MACD.get_macd_signal(data, signal_stats['short_ema_len'], signal_stats['long_ema_len'], signal_stats['signal_len'])
			except Exception as e:
				raise e

			#print(signals['MACD'][0], signals['MACD'][-1], signals['SIGNAL'][0], signals['SIGNAL'][-1])
			if signals['MACD'][-1] > signals['SIGNAL'][-1]:
				self._current_signal = 1
			elif signals['MACD'][-1] < signals['SIGNAL'][-1]:
				self._current_signal = -1
			else:
				self._current_signal = 0
		elif mode == 'SUPER':
			try:
				super_1 = SuperTrend.get_supertrend(data, 12, 3)['super_trend']
				super_2 = SuperTrend.get_supertrend(data, 10, 1)['super_trend']
				super_3 = SuperTrend.get_supertrend(data, 11, 2)['super_trend']
				ema = EMA.get_ema(data, 50)['ema']
			except Exception as e:
				raise e

			sup1 = 1 if super_1[-1] <= price else -1
			sup2 = 1 if super_2[-1] <= price else -1
			sup3 = 1 if super_3[-1] <= price else -1

			sup = sup1 + sup2 + sup3

			if (sup == 3) and (price > ema[-1]):
				self._current_signal = 1
			elif (sup == -3) and (price < ema[-1]):
				self._current_signal = -1
			else:
				self._current_signal = 0
			