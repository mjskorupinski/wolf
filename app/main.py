from app.data.instrument.provider import InstrumentProvider
import time

ip = InstrumentProvider()

ip.sync_instruments_data()

print(ip.get_instrument('AAPL'))

while ip._instrument_sync.is_syncing:
    time.sleep(1)