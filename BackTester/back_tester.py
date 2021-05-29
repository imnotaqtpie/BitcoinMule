import requests

from Signal.signal_generator import SignalGenerator

class BackTester:
	def __init__(self, symbol, pair):
		self._symbol = symbol
		self._pair = pair
		self._candles_url = "/market_data/candles"
		self._sg = SignalGenerator(self._symbol)

	def generate_historical_data(self, n_ticks, granularity):
		query = {'pair' : self._pair, 'interval' : granularity, 'limit' : n_ticks}
		data = requests.get(f"{DATA_URL}{self._candles_url}", params=query).json()
		print(query)
		open_ = list(reversed(list(map(itemgetter('open'), data))))
		high_ = list(reversed(list(map(itemgetter('high'), data))))
		low_ = list(reversed(list(map(itemgetter('low'), data))))
		close_ = list(reversed(list(map(itemgetter('close'), data))))
		vol_ = list(reversed(list(map(itemgetter('volume'), data))))

		self._data = {  'open' : open_, 
						'high' : high_,
						'low' : low_,
						'close' : close_,
						'volume' : vol_}

	def generate_signal(self, signal_mode, *args): 																						#Core logic here, return BUY, SELL or NEUTRAL depending on signal
		if signal_mode == 'MACD':
			self._sg.get_macd_signal(self._data, *args)
		elif signal_mode == 'BOLLINGER':
			self._sg.get_bollinger_bands(self._data, *args)
		else:
			return False


	def run_simulation(self, signal_mode, granularity, ticks, initial_resource, quantity):
		self.generate_historical_data(ticks, granularity)
		self.generate_signal(signal_mode, self._data)

		price = self._data['open']
		buy_prices = sell_prices = price

		currently_holding_buy = False
		currently_holding_ask = False
		current_inventory = 0
		current_resource = initial_resource
		total_turnover = 0
		round_trips = 0
		gross_pnl = []
		net_pnl = []
		pnl = 0
		pnl_arr = [0]
		total_pnl = 0
		entry_price = 0
		exit_flag = False

		for i in range(len(buy_prices)):
			if(current_resource < 0):
				break
			if(signal_mode == 'MACD'):
				if((self._macd[i] > self._sg._signal[i]) and (self._sg._rsi[i] < 80)):
					current_signal = 1
				elif((self._macd[i] < self._sg._signal[i]) and (self._sg._rsi[i] > 20 )):
					current_signal = -1
				else:
					current_signal = 0
			elif(signal_mode == 'BOLLINGER'):
				if(price[i] < self._sg._bollinger_low[i]):
					current_signal =  1
				elif(price[i] > self._sg._bollinger_high[i]):
					current_signal = -1
				else:
					current_signal = 0
				if((price[i] > self._sg._bollinger_high_high[i]) and (current_inventory < 0)):
					exit_flag = True
				if((price[i] < self._sg._bollinger_low_low[i]) and (current_inventory > 0)):
					exit_flag = True

			if current_inventory == 0:
				if current_signal > 0:
					current_inventory += quantity
					current_price = buy_prices[i]
					initial_resource = current_resource
					current_resource -= quantity * current_price
					total_turnover += quantity * current_price
					entry_price = current_price
					print(f"Taking buy entry at {current_price} | current resource : {current_resource}")
					continue
				elif current_signal < 0:
					current_inventory -= quantity
					current_price = sell_prices[i]
					initial_resource = current_resource
					current_resource += quantity * current_price
					total_turnover += quantity * current_price
					entry_price = current_price
					print(f"Taking sell entry at {current_price} | current resource : {current_resource}")
					continue
			elif current_inventory > 0:
				if current_signal < 0 or exit_flag == True:
					exit_flag = False
					current_inventory -= quantity
					current_price = sell_prices[i]
					current_resource += quantity * current_price
					total_turnover += quantity * current_price
					round_trips += 1
					gross_pnl.append(current_resource - initial_resource)
					cost = (current_price + entry_price) * 0.001 * quantity
					net_pnl.append(gross_pnl[-1] - cost)
					pnl += net_pnl[-1]
					pnl_arr.append(pnl)
					print(f"Taking buy exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
					continue
			elif current_inventory < 0:
				if current_signal > 0 or exit_flag == True:
					exit_flag = False
					current_inventory += quantity
					current_price = buy_prices[i]
					current_resource -= quantity * current_price
					total_turnover += quantity * current_price
					round_trips += 1
					gross_pnl.append(current_resource - initial_resource)
					cost = (current_price + entry_price) * 0.001 * quantity
					net_pnl.append(gross_pnl[-1] - cost)
					pnl += net_pnl[-1]
					pnl_arr.append(pnl)
					print(f"Taking sell exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
					continue

		if current_inventory > 0:
			current_inventory -= quantity
			current_price = sell_prices[-1]
			current_resource += quantity * current_price
			total_turnover += quantity * current_price
			gross_pnl.append(current_resource - initial_resource)
			cost = (current_price + entry_price) * 0.001 * quantity
			net_pnl.append(gross_pnl[-1] - cost)
			pnl += net_pnl[-1]
			pnl_arr.append(pnl)
			print(f"Taking buy exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
		elif current_inventory < 0:
			current_inventory -= quantity
			current_price = buy_prices[-1]
			current_resource -= quantity * current_price
			total_turnover += quantity * current_price
			gross_pnl.append(current_resource - initial_resource)
			cost = (current_price + entry_price) * 0.001 * quantity
			net_pnl.append(gross_pnl[-1] - cost)
			pnl += net_pnl[-1]
			pnl_arr.append(pnl)
			print(f"Taking sell exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
	
		print(f"\n\n\n\nGross pnl : {sum(gross_pnl)} | Net pnl : {sum(net_pnl)} | Round trips : {round_trips} | Win % : {len([p for p in net_pnl if p > 0]) * 100 / len(net_pnl)} | Sharpe : {np.mean(net_pnl) / np.std(net_pnl)} | Max pnl : {max(pnl_arr)} | Min Pnl : {min(pnl_arr)}")

		plt.plot(pnl_arr)
		plt.show()