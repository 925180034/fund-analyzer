from sqlalchemy import Column, String, Integer, DateTime, func
from backend.database import Base


class UserFund(Base):
    __tablename__ = "user_funds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)
    fund_code = Column(String(10), nullable=False, index=True)
    action = Column(String(20))  # 关注/持有/卖出
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
