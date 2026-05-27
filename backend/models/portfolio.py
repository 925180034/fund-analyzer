from sqlalchemy import Column, String, Float, Date, Integer, DateTime, ForeignKey, func
from backend.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(String(50), index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    fund_code = Column(String(10), ForeignKey("funds.code"), nullable=False, index=True)
    weight = Column(Float)           # 持仓权重(%)
    cost_price = Column(Float)       # 成本价
    shares = Column(Float)           # 持有份额
    buy_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
