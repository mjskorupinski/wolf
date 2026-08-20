from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.portfolio.asset import Portfolio, Asset  
from app.persistence.models import PortfolioModel, AssetModel


class PortfolioRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save(self, portfolio: Portfolio) -> None:
        stmt = select(PortfolioModel).where(PortfolioModel.name == portfolio.name)
        db_portfolio = self.db.execute(stmt).scalar_one_or_none()
        
        if not db_portfolio:
            db_portfolio = PortfolioModel(
                name=portfolio.name, 
                currency=portfolio.currency
            )
            self.db.add(db_portfolio)
            self.db.flush()

        db_portfolio.currency = portfolio.currency
        db_portfolio.assets.clear()

        for asset in portfolio._assets:
            db_asset = AssetModel(
                symbol=asset.symbol,
                volume=asset.volume,
                buy_price=asset.buy_price,
                currency=asset.currency,
                purchase_date=asset.purchase_date
            )
            db_portfolio.assets.append(db_asset)

        self.db.flush()

    def get_by_name(self, name: str, instrument_provider) -> Optional[Portfolio]:
        stmt = (
            select(PortfolioModel)
            .options(joinedload(PortfolioModel.assets))
            .where(PortfolioModel.name == name)
        )
        db_portfolio = self.db.execute(stmt).scalar_one_or_none()

        if not db_portfolio:
            return None

        portfolio = Portfolio(
            name=db_portfolio.name, 
            currency=db_portfolio.currency
        )
        
        for db_asset in db_portfolio.assets:
            instrument = instrument_provider.get_instrument(db_asset.symbol)
            
            asset = Asset(
                instrument=instrument,
                volume=db_asset.volume,
                buy_price=db_asset.buy_price,
                purchase_date=db_asset.purchase_date
            )
            portfolio.add(asset)

        return portfolio
        
    def get_all_portfolio_names(self) -> List[str]:
        stmt = select(PortfolioModel.name)
        return list(self.db.scalars(stmt).all())