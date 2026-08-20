from app.data.instrument.observer import InstrumentObserver
from app.data.instrument.symbols import INSTRUMENT_SYMBOLS

from app.persistence.repository.instrument import InstrumentRepository
from app.persistence.db import get_db
from app.tools.logger import get_logger
from app.tools.time import measure_exec_time

from threading import Lock, Thread
from concurrent.futures import ThreadPoolExecutor, as_completed

LOGGER = get_logger('instrumentDataSync')

class InstrumentDataSync:
    def __init__(self, max_workers: int = 5):
        self._max_workers = max_workers
        self._syncing = False
        self._lock = Lock()

    @property
    def is_syncing(self) -> bool:
        with self._lock:
            return self._syncing
    
    def sync_all(self, observers: list[InstrumentObserver]):
        with self._lock:
            if self._syncing:
                return
            self._syncing = True
            
        Thread(
            target=self._run_batch,
            args=(observers,),
            daemon=False
        ).start()

    def _run_batch(self, observers: list[InstrumentObserver]):
        try:
            self._execute_batch(observers)
            LOGGER.info(
                f"Instruments sync completed in time: {self._execute_batch.execution_time:.2f}s"
            )
        finally:
            with self._lock:
                self._syncing = False

    @measure_exec_time
    def _execute_batch(self, observers: list[InstrumentObserver]) :
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(self._sync_instrument, observer)
                for observer in observers
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    LOGGER.error(f'Unexpected error while syncing instrument data: {str(e)}')

    def _sync_instrument(self, observer: InstrumentObserver):
        with get_db() as session:
            repository = InstrumentRepository(session)
            observer.fetch_instrument_info(repository)
            observer.fetch_market_data(repository)
            observer.fetch_financial_statements(repository)
            observer.fetch_instrument_news(repository)


class InstrumentNotSupported(Exception):
    pass

class InstrumentProvider:
    def __init__(self, instrument_symbols = INSTRUMENT_SYMBOLS):
        self._observers: dict[str, InstrumentObserver] = {
            symbol: InstrumentObserver(symbol) for symbol in instrument_symbols
        }

        self._instrument_sync = InstrumentDataSync()

    @property
    def instrument_symbols(self):
        return list(self._observers.keys())

    def sync_instruments_data(self):
        self._instrument_sync.sync_all(self._observers.values())

    def get_instrument(self, symbol):
        with get_db() as session:
            repository = InstrumentRepository(session)
            return repository.get_full_instrument(symbol)
        
        return symbol
    
    def names_to_symbols(self) -> dict:
        names_to_symbols = {}