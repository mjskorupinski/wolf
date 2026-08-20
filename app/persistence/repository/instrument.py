import hashlib

from typing import Dict, Any, Optional, List
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.persistence.models import (
    InstrumentInfo,
    DailyMarketData,
    FinancialMetric,
    FinancialStatement,
    InstrumentNews,
)

class InstrumentRepository:
    def __init__(self, session: Session):
        self.db = session

    def save_instrument_info(self, symbol: str, info_data: Dict[str, Any]):
        inst = InstrumentInfo(
            symbol=symbol,
            short_name=info_data.get("shortName"),
            long_name=info_data.get("longName"),
            sector=info_data.get("sector"),
            industry=info_data.get("industry"),
            currency=info_data.get("currency"),
            summary=info_data.get("longBusinessSummary"),
        )
        self.db.merge(inst)
        self.db.flush()
    

    def save_daily_market_data(self, symbol: str, daily_market_data):
        record = DailyMarketData(
            symbol=symbol,
            trading_date=daily_market_data["trading_date"],
            open=daily_market_data.get("open"),
            high=daily_market_data.get("high"),
            low=daily_market_data.get("low"),
            close=daily_market_data.get("close"),
            volume=daily_market_data.get("volume"),
        )

        self.db.merge(record)
        self.db.flush() 


    def save_financial_metrics(self, symbol: str, metrics_data: Dict[str, Any]):
        metrics = FinancialMetric(
            symbol=symbol,
            trailing_pe=metrics_data.get("trailingPE"),
            forward_pe=metrics_data.get("forwardPE"),
            peg_ratio=metrics_data.get("pegRatio"),
            price_to_book=metrics_data.get("priceToBook"),
            dividend_yield=metrics_data.get("dividendYield"),
            beta=metrics_data.get("beta"),
            market_cap=metrics_data.get("marketCap"),
            total_revenue=metrics_data.get("totalRevenue"),
            revenue_growth=metrics_data.get("revenueGrowth"),
            ebitda=metrics_data.get("ebitda"),
            profit_margin=metrics_data.get("profitMargins"),
            total_debt=metrics_data.get("totalDebt"),
            quick_ratio=metrics_data.get("quickRatio"),
            return_on_equity=metrics_data.get("returnOnEquity"),
        )
        self.db.merge(metrics)
        self.db.flush()

    def save_financial_statement(self, symbol: str, statement_type: str, data: dict):
        record = FinancialStatement(
            symbol=symbol,
            statement_type=statement_type,
            data=data,
        )
        self.db.merge(record)
        self.db.flush()

    def save_news_article(self, symbol: str, article_data: Dict[str, Any]) -> InstrumentNews:
        url = article_data["url"].strip()
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

        news_record = InstrumentNews(
            url_hash=url_hash,
            symbol=symbol,
            title=article_data.get("title"),
            published_date=article_data.get("published_date"),
            source=article_data.get("source"),
            content=article_data.get("content"),
        )
        
        self.db.merge(news_record)
        self.db.flush()

    def get_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        stmt = select(InstrumentInfo).where(InstrumentInfo.symbol == symbol)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_symbols(self) -> List[str]:
        stmt = select(InstrumentInfo.symbol)
        return list(self.db.scalars(stmt).all())

    def get_financial_metrics(self, symbol: str) -> Optional[FinancialMetric]:
        stmt = select(FinancialMetric).where(FinancialMetric.symbol == symbol)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_daily_market_data(
        self, 
        symbol: str, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[DailyMarketData]:
        stmt = select(DailyMarketData).where(DailyMarketData.symbol == symbol)
        
        if start_date:
            stmt = stmt.where(DailyMarketData.trading_date >= start_date)
        if end_date:
            stmt = stmt.where(DailyMarketData.trading_date <= end_date)
            
        stmt = stmt.order_by(DailyMarketData.trading_date.asc())
        return list(self.db.scalars(stmt).all())
    
    def get_latest_market_data_date(self, symbol: str) -> Optional[date]:
        stmt = select(func.max(DailyMarketData.trading_date)).where(DailyMarketData.symbol == symbol)
        return self.db.execute(stmt).scalar()

    def get_financial_statement(self, symbol: str, statement_type: str) -> Optional[FinancialStatement]:
        stmt = select(FinancialStatement).where(
            FinancialStatement.symbol == symbol,
            FinancialStatement.statement_type == statement_type
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_news_articles(self, symbol: str, limit: int = 10) -> List[InstrumentNews]:
        stmt = (
            select(InstrumentNews)
            .where(InstrumentNews.symbol == symbol)
            .order_by(InstrumentNews.published_date.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_full_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        stmt = (
            select(InstrumentInfo)
            .options(
                joinedload(InstrumentInfo.financial_metrics),
                joinedload(InstrumentInfo.financial_statements),
            )
            .where(InstrumentInfo.symbol == symbol)
        )
        return self.db.execute(stmt).scalar_one_or_none()