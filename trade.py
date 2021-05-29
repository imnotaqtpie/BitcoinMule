from Runner.runner import Runner
from Common.utils import Utils

import time
import sys

symbol_name = "EnterSymbolNameHere"			#Name of coin to trade
resource_percent = 100 						#% of resources allocated to this coin, range (1,100)

base_log_dir = "EnterBaseLogDirHere"		#Output dir of logs

trade_log_path = f"{base_log_dir}/log_file_{symbol_name}_{time.time()}_trade.log"
error_log_path = f"{base_log_dir}/log_file_{symbol_name}_{time.time()}_error.log"

error_logger = Utils.setup_logger(error_log_path)

interval = '1m'								#Interval at which we generate data
limit = 100									#Number of historical data points to recover, max = 1000
w = 20										#Window length for bollinger band calculation
sd1 = 2										#Size of entry band
sd2 = 4										#Size of exit band

try:
	rn = Runner(symbol_name, resource_percent, trade_log_path, interval, limit, w, sd1, sd2, error_logger)
except Exception as e:
	error_logger.error(f"InitialisationFailedException : {e}")

	sys.exit(1)

while True:
	try:
		rn.run()
	except Exception as e:
		error_logger.error(f"RunningIterationFailedException : {e}")
		print("Error in run")
	time.sleep(30 - time.time() % 30)