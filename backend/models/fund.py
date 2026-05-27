from sqlalchemy import Column, String, Float, Date, DateTime, func
from backend.database import Base


class Fund(Base):
    __tablename__ = "funds"

    code = Column(String(10), primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(50), index=True)  # 股票型/混合型/债券型/指数型 etc.
    company = Column(String(100))           # 基金公司
    manager = Column(String(50))            # 基金经理
    establish_date = Column(Date)
    scale = Column(Float)                   # 基金规模(亿元)
    fee_buy = Column(Float)                 # 申购费率(%)
    fee_sell = Column(Float)                # 赎回费率(%)
    fee_manage = Column(Float)              # 管理费率(%)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
