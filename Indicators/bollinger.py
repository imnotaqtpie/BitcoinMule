import math

import numpy as np
import pandas as pd

class BollingerBands:
	@staticmethod
	def get_bollinger_bands(data, w, sd, back_test=True):
		if back_test == True:
			arr = data['close'].values
		else:
			arr = [a for a in reversed(data['close'])]

		df = pd.Series(arr)
		ma = df.rolling(w).mean()
		msd = df.rolling(w).std()

		bollinger_high = ma + (msd * sd)
		bollinger_low = ma - (msd * sd)

		bollinger_high = list(bollinger_high.dropna().values)
		bollinger_low = list(bollinger_low.dropna().values)

		l = len(bollinger_high)
		for i in range(len(arr) - l):
			bollinger_high.insert(0,0)
			bollinger_low.insert(0,0)

		return {"bollinger_low" : bollinger_low, 
				"bollinger_high" : bollinger_high}