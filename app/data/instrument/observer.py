import pandas as pd

from datetime import timedelta, date

from yfinance import Ticker
from newspaper import Article

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.persistence.repository.instrument import InstrumentRepository
from app.tools.logger import get_logger

LOGGER = get_logger('instrumentObserver', to_file=False)

class InstrumentObserver:
    def __init__(self, symbol: str):
        self._symbol = symbol.upper()

    @property
    def symbol(self):
        return self._symbol
    
    def _get_ticker(self) -> Ticker:
        return Ticker(self.symbol)

    def fetch_instrument_info(self, repository: InstrumentRepository):
        ticker = self._get_ticker()

        try:
            LOGGER.info(f'Syncing instrument info for symbol {self.symbol}...')

            info = ticker.info
            repository.save_instrument_info(self.symbol, info)
            repository.save_financial_metrics(self.symbol, info)

            LOGGER.info(f'Successfully synced instrument info for symbol {self.symbol}.')
        except Exception as e:
            LOGGER.error(f'Error while syncing instrument info for symbol {self.symbol}: {str(e)}')

    def fetch_market_data(self, repository: InstrumentRepository):
        ticker = self._get_ticker()

        try:
            LOGGER.info(f'Syncing market data for symbol {self.symbol}...')

            latest_date = repository.get_latest_market_data_date(self.symbol)

            if latest_date:
                start_date = latest_date + timedelta(days=1)
                
                if start_date >= date.today():
                    return

                df = ticker.history(start=start_date.strftime("%Y-%m-%d"))
            else:
                df = ticker.history(period="max")

            if df is None or df.empty:
                return

            df = df.reset_index()

            for _, row in df.iterrows():
                trading_date = pd.to_datetime(row["Date"]).date()

                daily_data = {
                    "trading_date": trading_date,
                    "open": row.get("Open"),
                    "high": row.get("High"),
                    "low": row.get("Low"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume")
                }
                
                repository.save_daily_market_data(self.symbol, daily_data)

            LOGGER.info(f'Successfully synced market data for symbol {self.symbol}.')
        except Exception as e:
            LOGGER.error(f'Error while syncing market data for symbol {self.symbol}: {str(e)}')

    def fetch_financial_statements(self, repository: InstrumentRepository):
        ticker = self._get_ticker()

        try: 
            LOGGER.info(f'Syncing financial statements for symbol {self.symbol}...')

            statements = {
                'income': ticker.income_stmt,
                'balance_sheet': ticker.balance_sheet,
                'cashflow': ticker.cashflow
            }

            for type, statement in statements.items():
                if statement is not None and not statement.empty:
                    stmnt_copy = statement.copy()
                    stmnt_copy.columns = pd.to_datetime(stmnt_copy.columns).strftime("%Y")
                    
                    stmnt_dict = stmnt_copy.to_dict(orient="index")
                    repository.save_financial_statement(self.symbol, type, stmnt_dict)

            LOGGER.info(f'Successfully synced financial statements for symbol {self.symbol}.')
        except Exception as e:
            LOGGER.error(f'Error while syncing financial statements for symbol {self.symbol}: {str(e)}')

    def fetch_instrument_news(self, repository: InstrumentRepository, max_workers: int = 5):
        ticker = self._get_ticker()

        try: 
            LOGGER.info(f'Syncing instrument news for symbol {self.symbol}...')
            news = ticker.news

            if not news:
                return
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._parse_article, news_data) for news_data in news]
                for future in as_completed(futures):
                    article = future.result()
                    if article:
                        repository.save_news_article(
                            symbol=self.symbol, 
                            article_data=article
                        )

            LOGGER.info(f'Successfully synced instrument news for symbol {self.symbol}.')
        except Exception as e:
            LOGGER.error(f'Error while syncing instrument news for symbol {self.symbol}: {str(e)}')

    def _parse_article(self, article_data) -> dict:
        metadata = article_data.get('content', {})

        url = metadata.get('clickThroughUrl', {}).get('url')

        content = ''
        if url:
            article = Article(url)
            article.download()
            article.parse()

            content = article.text

        return {
            "url": url,
            "title": metadata.get('title'),
            "date": metadata.get('pubDate'),
            "source": metadata.get('provider', {}).get('displayName'),
            "content": content
        }
    

    def get_current_market_data(self) -> dict:
        ticker = self._get_ticker()

        info = ticker.info
        return {
            "current_price": info.get("currentPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open"),
            "day_low": info.get("dayLow"),
            "day_high": info.get("dayHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "volume": info.get("volume"),
            "average_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap")
        }