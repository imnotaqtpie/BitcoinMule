from Common.utils import Utils
from Common.urls import URL
from Common.order_side import OrderSide

from Symbol.symbol_generator import SymbolGenerator

from Data.data_generator import DataGenerator

from Signal.signal_generator import SignalGenerator

from Execution.execution import Execution
from OMS.oms import OMS

class Runner:
	def __init__(self, symbol_name, resource_percent, log_path, interval, limit, signal_mode, signal_stats, target, stop_loss, trail_loss, error_logger, trade_logger, mode='Paper'):
		self._error_logger = error_logger
		self._trade_logger = trade_logger
		self._mode = mode
		try:
			self.create_supporting_objects(symbol_name, log_path, resource_percent, target, stop_loss, trail_loss)
		except Exception as e:
			self._error_logger.error(f"SupportingObjectCreationError : {e}")
			raise Exception("SupportingObjectCreationException")

		self._interval = interval
		self._limit = limit
		self._signal_mode = signal_mode
		self._signal_stats = signal_stats

	def create_supporting_objects(self, symbol_name, log_path, resource_percent, target, stop_loss, trail_loss):
		self._sg = SymbolGenerator(symbol_name, self._error_logger)
		self._dg = DataGenerator(self._sg)
		self._sig = SignalGenerator()
		self._oms = OMS(symbol_name, self._trade_logger, self._error_logger)
		self._exec = Execution(self._sg, resource_percent, target, stop_loss, trail_loss, self._oms, self._mode)
		
	def run(self):
		retry_count = 3
		try:
			self._dg.get_symbol_data(self._interval, self._limit)
		except Exception as e:
			self._error_logger.error(f"DataGenerationError : {e}")
			return False

		ltp = self._dg.get_ltp()
		try:
			self._sig.generate_signal(self._dg._data, self._signal_mode, float(ltp['last_price']), self._signal_stats)
		except Exception as e:
			for i in range(retry_count):
				self._error_logger.warning(f"SignalGenerationError : {e} | Retrying | {retry_count - i} tries left")
				ltp = self._dg.get_ltp()
				if ltp['bid'] == None or ltp['ask'] == None or ltp['last_price'] == None:
					continue
				break
			if ltp['bid'] == None or ltp['ask'] == None or ltp['last_price'] == None:
				return
		
		signal = self._sig._current_signal
		try:
			self._exec.set_action(signal, float(ltp['bid']), float(ltp['ask']))
		except Exception as e:
			self._error_logger.error(f"OrderPlacingError : {e}")

	def end_run(self):
		self._exec.place_exit_order(float(self._dg.get_ltp()['last_price']))
		self._error_logger.info("RUN COMPLETE!")