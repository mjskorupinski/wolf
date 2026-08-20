from datetime import datetime

from sqlalchemy import (
    BIGINT,
    DECIMAL,
    TEXT,
    VARCHAR,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Float,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from typing import List, Optional


class Base(DeclarativeBase):
    pass


class InstrumentInfo(Base):
    __tablename__ = "instruments"

    symbol: Mapped[str] = mapped_column(VARCHAR(20), primary_key=True)
    short_name: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    long_name: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(VARCHAR(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(VARCHAR(100), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(VARCHAR(10), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    market_data: Mapped[List["DailyMarketData"]] = relationship(
        "DailyMarketData", back_populates="instrument", cascade="all, delete-orphan"
    )
    financial_metrics: Mapped[List["FinancialMetric"]] = relationship(
        "FinancialMetric", back_populates="instrument", cascade="all, delete-orphan"
    )
    financial_statements: Mapped[List["FinancialStatement"]] = relationship(
        "FinancialStatement", back_populates="instrument", cascade="all, delete-orphan"
    )
    news_articles: Mapped[List["InstrumentNews"]] = relationship(
        "InstrumentNews", back_populates="instrument", cascade="all, delete-orphan"
    )


class DailyMarketData(Base):
    __tablename__ = "daily_market_data"

    symbol: Mapped[str] = mapped_column(
        VARCHAR(20), ForeignKey("instruments.symbol", ondelete="CASCADE"), primary_key=True
    )
    trading_date: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    open: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4), nullable=True)
    high: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4), nullable=True)
    low: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4), nullable=True)
    close: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 4), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)

    instrument: Mapped["InstrumentInfo"] = relationship("InstrumentInfo", back_populates="market_data")

    __table_args__ = (
        Index("idx_daily_market_data_symbol_date", "symbol", "trading_date"),
    )


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(
        VARCHAR(20), ForeignKey("instruments.symbol", ondelete="CASCADE"), index=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    trailing_pe: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    forward_pe: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    peg_ratio: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    price_to_book: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    dividend_yield: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    beta: Mapped[Optional[float]] = mapped_column(DECIMAL(8, 4), nullable=True)
    market_cap: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)

    total_revenue: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)
    revenue_growth: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    ebitda: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)
    profit_margin: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    total_debt: Mapped[Optional[int]] = mapped_column(BIGINT, nullable=True)
    quick_ratio: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)
    return_on_equity: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), nullable=True)

    instrument: Mapped["InstrumentInfo"] = relationship("InstrumentInfo", back_populates="financial_metrics")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    symbol: Mapped[str] = mapped_column(
        VARCHAR(20), ForeignKey("instruments.symbol", ondelete="CASCADE"), primary_key=True
    )
    statement_type: Mapped[str] = mapped_column(
        VARCHAR(50), primary_key=True
    )
    
    data: Mapped[dict] = mapped_column(JSON)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    instrument: Mapped["InstrumentInfo"] = relationship("InstrumentInfo", back_populates="financial_statements")


class InstrumentNews(Base):
    __tablename__ = "instrument_news"

    url_hash: Mapped[str] = mapped_column(VARCHAR(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(VARCHAR(20), ForeignKey("instruments.symbol"))
    title: Mapped[Optional[str]] = mapped_column(VARCHAR(500))
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source: Mapped[Optional[str]] = mapped_column(VARCHAR(100))
    content: Mapped[Optional[str]] = mapped_column(TEXT)

    instrument: Mapped["InstrumentInfo"] = relationship("InstrumentInfo", back_populates="news_articles")


class PortfolioModel(Base):
    __tablename__ = 'portfolios'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    assets: Mapped[list["AssetModel"]] = relationship(
        back_populates="portfolio", 
        cascade="all, delete-orphan"
    )


class AssetModel(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    volume: Mapped[float] = mapped_column(Float)
    buy_price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String)
    purchase_date: Mapped[datetime] = mapped_column(DateTime)

    portfolio: Mapped["PortfolioModel"] = relationship(back_populates="assets")