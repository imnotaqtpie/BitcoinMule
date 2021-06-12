import requests
import os 
import datetime 
import time 

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import dateutil.relativedelta

from Symbol.symbol_generator import SymbolGenerator
from Common.utils import Utils

from Indicators.macd import MACD
from Indicators.bollinger import BollingerBands
from Indicators.super_trend import SuperTrend
from Indicators.ema import EMA
from Indicators.ma import MA 

class BackTester:
	def __init__(self, symbol, data_path, log_path):
		self._symbol = symbol
		self._logger =  Utils.setup_logger(os.path.join(log_path, f"sim_log_file_{symbol}_{time.time()}_trade.log"))
		self._sg = SymbolGenerator(symbol, self._logger)
		self._data_path = data_path
		self._epoch_start = datetime.datetime(1970,1,1)

	def get_historical_data(self, granularity, start_time, stop_time):
		file_path = os.path.join(self._data_path, f"{self._symbol}_{granularity}.csv")
		price_df = pd.read_csv(file_path, names=["timestamp", "open", "high", "low", "close", "volume", "trades"]).set_index("timestamp")
		start_time_epc = int((datetime.datetime.strptime(start_time, "%d-%m-%Y") - self._epoch_start).total_seconds())
		stop_time_epc = int((datetime.datetime.strptime(stop_time, "%d-%m-%Y") - self._epoch_start).total_seconds())
		
		return price_df.loc[start_time_epc:stop_time_epc]
	
	def set_quantity(self, price, current_resource):
		if price == 0:
			raise Exception("InvalidPriceError")

		qty = (current_resource / price)
		min_qty = self._sg._symbol_details['min_quantity']
		return round(int(qty / min_qty) * min_qty, 5)

	def run_simulation(self, data, signal_mode, signal_stats, target, stop, trail, starting_resource, portfolio_stop):
		price = data['close'].values
		open_ = data['open'].values
		high_ = data['high'].values
		low_ = data['low'].values
		close_ = data['close'].values
		ts = data.index

		if signal_mode == "BOLLINGER":
			signals = BollingerBands.get_bollinger_bands(data, signal_stats['w'], signal_stats['sd'], back_test=True)
		if signal_mode == "MACD":
			signals = MACD.get_macd_signal(data, signal_stats['short_ema_len'], signal_stats['long_ema_len'], signal_stats['signal_len'], back_test=True)
			ema = EMA.get_ema(data, 200, back_test=True)['ema']
		if signal_mode == "SUPER":
			sp1 = SuperTrend.get_supertrend(data, 12, 3, back_test=True)['super_trend']
			sp2 = SuperTrend.get_supertrend(data, 10, 1, back_test=True)['super_trend']
			sp3 = SuperTrend.get_supertrend(data, 11, 2, back_test=True)['super_trend']
			ema = EMA.get_ema(data, 200, back_test=True)['ema']

		current_inventory = 0
		current_resource = starting_resource
		total_turnover = 0

		round_trips = 0
		gross_pnl = []
		net_pnl = []
		pnl = 0
		pnl_arr = [0]
		total_pnl = 0
		entry_price = 0
		max_price = 0
		min_price = float("inf")
		exit_flag = False
		i = 0
		for i in range(1,len(price)):
			if(current_resource <= (1 - portfolio_stop / 100) * starting_resource and current_inventory == 0):
				dt1 = datetime.datetime.fromtimestamp(ts[0])
				dt2 = datetime.datetime.fromtimestamp(ts[i])
				rd = dateutil.relativedelta.relativedelta (dt2, dt1)

				time = f"{rd.years} years, {rd.months} months, {rd.days} days, {rd.hours} hours, {rd.minutes} minutes and {rd.seconds} seconds"
				print(f"Out of funds! Time ran {time}")
				break
			
			if(signal_mode == 'BOLLINGER'):
				if(price[i] < signals['bollinger_high'][i]):
					current_signal = -1
				elif(price[i] > signals['bollinger_low'][i]):
					current_signal = 1
				else:
					current_signal = 0

			elif(signal_mode == "MACD"):
				if signals['MACD'][i] > signals['SIGNAL'][i] and price[i] > ema[i]:
					current_signal = 1
				elif signals['MACD'][i] < signals['SIGNAL'][i] and price[i] > ema[i]:
					current_signal = -1
				else:
					current_signal = 0

				if current_inventory > 0 and signals['MACD'][i] < signals['SIGNAL'][i]:
					exit_flag = True
				elif current_inventory < 0 and signals['MACD'][i] > signals['SIGNAL'][i]:
					exit_flag = True

			elif(signal_mode == "SUPER"):
				sup1 = 1 if sp1[i] <= price[i] else -1
				sup2 = 1 if sp3[i] <= price[i] else -1
				sup3 = 1 if sp2[i] <= price[i] else -1

				sup = sup1 + sup2 + sup3

				if (sup == 3):
					current_signal = 1
				if (sup == -3):
					current_signal = -1
				else:
					current_signal = 0
				
				if current_inventory > 0 and sup == -3:
					exit_flag = True
				elif current_inventory < 0 and sup == 3:
					exit_flag = True

			elif(signal_mode == 'TREND'):
				if ((close_[i-1] - open_[i-1]) * 100 / open_[i-1]) >= 1:
					current_signal = 1
				elif ((close_[i-1] - open_[i-1]) * 100 / open_[i-1]) <= -1:
					current_signal = -1
				else:
					current_signal = 0

				if current_inventory > 0 and (close_[i-1] < open_[i-1]):
					exit_flag = True
				elif current_inventory < 0 and (close_[i-1] > open_[i-1]):
					exit_flag = True



			if current_inventory == 0:
				if current_signal > 0:
					current_price = price[i]
					quantity = self.set_quantity(current_price, current_resource)
					current_inventory += quantity
					initial_resource = current_resource
					current_resource -= quantity * current_price
					total_turnover += quantity * current_price
					entry_price = current_price
					stats = {	"TIMESTAMP" : datetime.datetime.fromtimestamp(ts[i]).strftime("%d-%m-%Y %H:%M:%S"),
								"SIDE" : 'BUY',
								"QTY" : quantity, 
								"PRICE" : current_price,
								"INV" : current_inventory,
								"PNL" : pnl}
					self._logger.info(f"Taking buy entry at {current_price} | current resource : {current_resource}")
					self._logger.info(stats)
					continue
				elif current_signal < 0:
					current_price = price[i]
					quantity = self.set_quantity(current_price, current_resource)
					if quantity == 0:
						print("Out of funds!")
					current_inventory -= quantity
					initial_resource = current_resource
					current_resource += quantity * current_price
					total_turnover += quantity * current_price
					entry_price = current_price
					stats = {	"TIMESTAMP" : datetime.datetime.fromtimestamp(ts[i]).strftime("%d-%m-%Y %H:%M:%S"),
								"SIDE" : 'SELL',
								"QTY" : quantity, 
								"PRICE" : current_price,
								"INV" : current_inventory,
								"PNL" : pnl}
					self._logger.info(f"Taking sell entry at {current_price} | current resource : {current_resource}")
					self._logger.info(stats)
					continue
			elif current_inventory > 0:
				if exit_flag == True:
					exit_flag = False
					quantity = current_inventory
					if quantity == 0:
						print("Out of funds!")
					current_inventory = 0
					current_price = price[i]
					current_resource += quantity * current_price
					total_turnover += quantity * current_price
					round_trips += 1
					gross_pnl.append(current_resource - initial_resource)
					cost = (current_price + entry_price) * 0.001 * quantity 
					net_pnl.append(gross_pnl[-1] - cost)
					current_resource = starting_resource + pnl
					pnl += net_pnl[-1]
					pnl_arr.append(pnl)
					max_price = 0
					stats = {	"TIMESTAMP" : datetime.datetime.fromtimestamp(ts[i]).strftime("%d-%m-%Y %H:%M:%S"),
								"SIDE" : 'SELL',
								"QTY" : quantity, 
								"PRICE" : current_price,
								"INV" : current_inventory,
								"PNL" : pnl}
					self._logger.info(f"Taking buy exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
					self._logger.info(stats)
					continue
			elif current_inventory < 0:
				if exit_flag == True:
					exit_flag = False
					quantity = -1 * current_inventory
					current_inventory = 0
					current_price = price[i]
					current_resource -= quantity * current_price
					total_turnover += quantity * current_price
					round_trips += 1
					gross_pnl.append(current_resource - initial_resource)
					cost = (current_price + entry_price) * 0.001 * quantity
					net_pnl.append(gross_pnl[-1] - cost)
					current_resource = starting_resource + pnl
					pnl += net_pnl[-1]
					pnl_arr.append(pnl)
					min_price = float("inf")
					stats = {	"TIMESTAMP" : datetime.datetime.fromtimestamp(ts[i]).strftime("%d-%m-%Y %H:%M:%S"),
								"SIDE" : 'BUY',
								"QTY" : quantity, 
								"PRICE" : current_price,
								"INV" : current_inventory,
								"PNL" : pnl}
					self._logger.info(f"Taking sell exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
					self._logger.info(stats)
					continue

		if current_inventory > 0:
			quantity = current_inventory
			current_inventory = 0
			current_price = price[i]
			current_resource += quantity * current_price
			total_turnover += quantity * current_price
			gross_pnl.append(current_resource - initial_resource)
			cost = (current_price + entry_price) * 0.001 * quantity
			net_pnl.append(gross_pnl[-1] - cost)
			pnl += net_pnl[-1]
			pnl_arr.append(pnl)
			stats = {	"TIMESTAMP" : datetime.datetime.fromtimestamp(ts[i]).strftime("%d-%m-%Y %H:%M:%S"),
						"SIDE" : 'SELL',
						"QTY" : quantity, 
						"PRICE" : current_price,
						"INV" : current_inventory,
						"PNL" : pnl}
			self._logger.info(f"Taking buy exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
			self._logger.info(stats)
		elif current_inventory < 0:
			quantity = -1 * current_inventory
			current_inventory = 0
			current_price = price[i]
			current_resource -= quantity * current_price
			total_turnover += quantity * current_price
			gross_pnl.append(current_resource - initial_resource)
			cost = (current_price + entry_price) * 0.001 * quantity
			net_pnl.append(gross_pnl[-1] - cost)
			pnl += net_pnl[-1]
			pnl_arr.append(pnl)
			stats = {	"TIMESTAMP" : datetime.datetime.fromtimestamp(ts[i]).strftime("%d-%m-%Y %H:%M:%S"),
						"SIDE" : 'BUY',
						"QTY" : quantity, 
						"PRICE" : current_price,
						"INV" : current_inventory,
						"PNL" : pnl}
			self._logger.info(f"Taking sell exit at {current_price} | current resource : {current_resource} | trade pnl : {current_resource - initial_resource}")
			self._logger.info(stats)

		print(f"\n\n\n\nGross pnl : {sum(gross_pnl)} | Net pnl : {sum(net_pnl)} | Round trips : {round_trips} | Win % : {len([p for p in net_pnl if p > 0]) * 100 / len(net_pnl)} | Sharpe : {np.mean(net_pnl) / np.std(net_pnl)} | Max pnl : {max(pnl_arr)} | Min Pnl : {min(pnl_arr)}")
		plt.plot(pnl_arr)
		plt.show()
		return sum(net_pnl), len([p for p in net_pnl if p > 0]) * 100 / len(net_pnl), np.mean(net_pnl) / np.std(net_pnl), round_trips