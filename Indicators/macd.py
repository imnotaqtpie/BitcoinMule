import math

import numpy as np
import pandas as pd

class MACD:
	@staticmethod
	def get_macd_signal(data, short_ema_len, long_ema_len, signal_len, back_test = False):
		if back_test == True:
			arr = data['close'].values
		else:
			arr = [a for a in reversed(data['close'])]
			
		price = pd.Series(arr)
		exp1 = price.ewm(span=long_ema_len, adjust=False).mean()
		exp2 = price.ewm(span=short_ema_len, adjust=False).mean()

		macd = exp2 - exp1

		signal = macd.ewm(span=signal_len, adjust=False).mean()
		
		return 	{"MACD" : macd.values, 
		 	 	 "SIGNAL" : signal.values}

