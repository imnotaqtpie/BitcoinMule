from BackTester.back_tester import BackTester
import json 


config_path = "D:/CryptoBot/backtest_config.json"

with open(config_path) as f:
	cfg = json.loads(f.read())

print(cfg) 


symbol = cfg["symbol"]																			#Symbol to backtest the strategy for
data_path = cfg["data_path"]																	#Path of the historical data in csv format
log_path = cfg["log_path"]																		#Path to the dir storing logfiles for simulated runs
granularity = cfg["granularity"]																#Granularity of OHLC in minutes
start_time = cfg["start_time"]																	#Start time of the simulated run
stop_time = cfg["stop_time"]																	#Stop time of the simulated run

signal_mode = cfg["signal_mode"]																#Mode of the signal (Strategy)
args = 	cfg["args"]																				#Arguments for selected signal mode
		 
target = cfg["target"]																			#% target profit per trade
stop = cfg["target"]																			#% stop loss per trade
trail = cfg["target"]																			#% trailing stop loss
	
portfolio_stop = cfg["portfolio_stop"]															#% of portfolio loss at which strategy stops
initial_resource = cfg["initial_resource"]														#Initial capital to start with


bt = BackTester(symbol, data_path, log_path)
data = bt.get_historical_data(granularity, start_time, stop_time)

bt.run_simulation(data, signal_mode, args, target, stop, trail, initial_resource, portfolio_stop)