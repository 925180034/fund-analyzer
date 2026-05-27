from sqlalchemy import Column, String, Integer, Float, Date, DateTime, func
from backend.database import Base


class UserFund(Base):
    __tablename__ = "user_funds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    fund_code = Column(String(10), nullable=False, index=True)
    action = Column(String(20))  # 关注/持有/卖出
    buy_price = Column(Float, nullable=True)    # 买入价格
    buy_date = Column(Date, nullable=True)      # 买入日期
    amount = Column(Float, nullable=True)       # 持有份额
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
