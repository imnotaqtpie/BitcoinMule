from Common.utils import Utils
from Common.urls import URL
from Common.order_side import OrderSide

from Symbol.symbol_generator import SymbolGenerator

from Data.data_generator import DataGenerator

from Signal.signal_generator import SignalGenerator

from Execution.execution import Execution
from OMS.oms import OMS

class Runner:
	def __init__(self, symbol_name, resource_percent, log_path, interval, limit, w, sd1, sd2, error_logger):
		self._error_logger = error_logger
		try:
			self.create_supporting_objects(symbol_name, log_path, resource_percent)
		except Exception as e:
			self._error_logger.error(f"SupportingObjectCreationError : {e}")
			raise Exception("SupportingObjectCreationException")

		self._interval = interval
		self._limit = limit
		self._w = w 
		self._sd1 = sd1
		self._sd2 = sd2

	def create_supporting_objects(self, symbol_name, log_path, resource_percent):
		self._sg = SymbolGenerator(symbol_name, self._error_logger)
		self._dg = DataGenerator(self._sg)
		self._sig = SignalGenerator()
		self._oms = OMS(symbol_name, log_path)
		self._exec = Execution(self._sg, resource_percent, self._oms)
		
	def run(self):
		try:
			self._dg.get_symbol_data(self._interval, self._limit)
		except Exception as e:
			self._error_logger.error(f"DataGenerationError : {e}")
			return False

		ltp = self._dg.get_ltp()
		try:
			self._sig.generate_signal(self._dg._data, self._w, self._sd1, self._sd2, float(ltp['last_price']))
		except Exception as e:
			self._error_logger.error(f"SignalGenerationError : {e}")
		
		signal = self._sig._current_signal
		exit_buy = self._sig._exit_flag_buy
		exit_sell = self._sig._exit_flag_sell

		print(f"LTP generated || signal : {signal} || exit_buy : {exit_buy} || exit_sell : {exit_sell} || ltp : {ltp['last_price']}")
		
		try:
			self._exec.set_action(signal, float(ltp['bid']), float(ltp['ask']), exit_buy, exit_sell)
		except Exception as e:
			self._error_logger.error(f"OrderPlacingError : {e}")