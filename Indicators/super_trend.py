import math

import numpy as np
import pandas as pd

class SuperTrend:
	@staticmethod
	def get_supertrend(data, atr_len, mult, back_test=False):
		if back_test == True:
			close = data['close'].values
			low = data['low'].values
			high = data['high'].values
		else:
			close = [a for a in reversed(data['close'])]
			low = [a for a in reversed(data['low'])]
			high = [a for a in reversed(data['high'])]
		
		tr = []

		for i in range(len(close)):
			tr.append(max((high[i] - low[i]), abs(high[i] - close[i]), abs(low[i] - close[i])))
		
		tr_s = pd.Series(tr)
		atr = tr_s.ewm(span=atr_len, adjust=False).mean().values

		basic_upper = []
		basic_lower = []
		for i in range(len(close)):
			basic_upper.append((high[i] + low[i]) / 2 + (mult * atr[i]))
			basic_lower.append((high[i] + low[i]) / 2 - (mult * atr[i]))

		final_upper = []
		final_lower = []

		for i in range(len(close)):
			if i == 0:
				final_lower.append(0)
				final_upper.append(0)
			else:
				if (basic_upper[i] < final_upper[i-1]) or (close[i-1] > final_upper[i-1]):
					final_upper.append(basic_upper[i])
				else:
					final_upper.append(final_upper[i-1])

				if (basic_lower[i] > final_lower[i-1]) or (close[i-1] < final_lower[i-1]):
					final_lower.append(basic_lower[i])
				else:
					final_lower.append(final_lower[i-1])

		super_trend = []

		for i in range(len(close)):
			if i == 0:
				super_trend.append(0)
			else:
				if (super_trend[i-1] == final_upper[i-1]) and (close[i] <= final_upper[i]):
					super_trend.append(final_upper[i])
				elif(super_trend[i-1] == final_upper[i-1]) and (close[i] > final_upper[i]):
					super_trend.append(final_lower[i])
				elif(super_trend[i-1] == final_lower[i-1]) and (close[i] >= final_lower[i]):
					super_trend.append(final_lower[i])
				elif(super_trend[i-1] == final_lower[i-1]) and (close[i] < final_lower[i]):
					super_trend.append(final_upper[i])

		return {"super_trend" : super_trend}