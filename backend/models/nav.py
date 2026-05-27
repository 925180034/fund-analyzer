from sqlalchemy import Column, String, Float, Date, Integer, Index
from backend.database import Base


class NavHistory(Base):
    __tablename__ = "nav_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    nav = Column(Float)        # 单位净值
    acc_nav = Column(Float)    # 累计净值
    growth = Column(Float)     # 日增长率(%)

    __table_args__ = (
        Index("ix_nav_code_date", "code", "date", unique=True),
    )
