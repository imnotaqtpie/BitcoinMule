import math

import numpy as np
import pandas as pd

class EMA:
	@staticmethod
	def get_ema(data, ema_len, back_test=False):
		if back_test == True:
			arr = data['close'].values
		else:
			arr = [a for a in reversed(data['close'])]

		price = pd.Series(arr)
		ema = price.ewm(span=ema_len, adjust=False).mean()
		
		return 	{"ema" : ema.values}