from sqlalchemy import Column, String, Float, Date, Integer, Index
from backend.database import Base


class FundRanking(Base):
    __tablename__ = "fund_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True)
    rank_date = Column(Date, nullable=False, index=True)
    type = Column(String(50), index=True)   # 基金类型
    rank_3m = Column(Integer)                # 近3月排名
    rank_6m = Column(Integer)                # 近6月排名
    rank_1y = Column(Integer)                # 近1年排名
    rank_3y = Column(Integer)                # 近3年排名
    total_count = Column(Integer)            # 同类基金总数

    __table_args__ = (
        Index("ix_ranking_code_date", "code", "rank_date", unique=True),
    )
