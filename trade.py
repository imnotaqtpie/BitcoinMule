from Runner.runner import Runner
from Common.utils import Utils

import json
import time
import sys

config_path = "D:/CryptoBot/trade_config.json"

with open(config_path) as f:
	cfg = json.loads(f.read())

symbol_name = cfg["symbol"]																			#Target instrument to trade on
resource_percent = cfg["resource_percent"]															#% of resources to be exposed per trade

base_log_path = cfg["base_log_path"]																#Base path for storing the logs

interval = cfg["granularity"]																		#OHLC candle stick size
limit = cfg["limit"]																				#Number of historical candlesticks to be retrieved

signal_mode = cfg["signal_mode"]																	#Mode of the signal
signal_args = cfg["args"]																			#Params corresponding to the signal mode
 
mode = cfg["run_mode"]																				#Running mode, can be either Live or Paper

target = cfg["target"]																				#% target profit per trade
stop_loss = cfg["stop"]																				#% stop loss per trade
trail_loss = cfg["trail"]																			#% trailing stop loss

run_interval = cfg["run_interval"]																	#Time interval in seconds to check signal and place order

trade_log_path = f"{base_log_path}/log_file_{symbol_name}_{time.time()}_trade.log"
error_log_path = f"{base_log_path}/log_file_{symbol_name}_{time.time()}_error.log"

error_logger = Utils.setup_logger(error_log_path)
trade_logger = Utils.setup_logger(trade_log_path)

print(f"Starting run with following params : SYMBOL : {symbol_name} | RESOURCE_PERCENT : {resource_percent} | GRANULARITY : {interval} | LIMIT : {limit} | \
											 SIGNAL MODE : {signal_mode} | SIGNAL ARGS : {signal_args} | RUN MODE : {mode} |\
											 TARGET : {target} | STOP LOSS : {stop_loss} | TRAIL LOSS : {trail_loss} | RUN INTERVAL : {run_interval} | \
											 TRADES LOG : {trade_log_path} | ERROR LOGS : {error_log_path}")

try:
	rn = Runner(symbol_name, resource_percent, trade_log_path, interval, limit, signal_mode, signal_args, target, stop_loss, trail_loss, error_logger, trade_logger, mode)
except Exception as e:
	error_logger.error(f"InitialisationFailedException : {e}")
	sys.exit(1)

try:
	while True:
		try:
			rn.run()
		except Exception as e:
			error_logger.error(f"RunningIterationFailedException : {e}")
			print("Error in run")
		time.sleep(run_interval - time.time() % run_interval)
except KeyboardInterrupt:
	print("Ending!")
	rn.end_run()
	error_logger.info(f"PNL : {rn._exec._current_net_pnl} | ROUND TRIPS : {rn._exec._round_trips}")
	sys.exit(1)
		