import math

import numpy as np
import pandas as pd

class MA:
	@staticmethod
	def get_ma(data, ma_len, back_test=False):
		if back_test == True:
			arr = data['close'].values
		else:
			arr = [a for a in reversed(data['close'])]
		price = pd.Series(arr)
		ma = price.ewm(span=ma_len, adjust=False).mean()
		
		return 	{"ma" : ma.values}