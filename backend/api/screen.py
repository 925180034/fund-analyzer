from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from backend.database import get_db
from backend.models import Fund, FundRanking
from backend.services.fund_screener import calculate_4433_score, screen_funds_4433
from backend.services.cache_manager import cache_get, cache_set

router = APIRouter(prefix="/screen", tags=["筛选"])


@router.get("/4433")
async def screen_4433(
    fund_type: Optional[str] = Query(None, description="基金类型"),
    min_score: float = Query(50, description="最低得分"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """4433 筛选基金"""
    cache_key = f"screen:4433:{fund_type}:{min_score}:{page}:{size}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    # 获取最新排名数据
    subq = (
        select(FundRanking.code, select(func.max(FundRanking.rank_date)).scalar_subquery().label("max_date"))
        .group_by(FundRanking.code)
    )

    query = select(FundRanking)
    if fund_type:
        query = query.where(FundRanking.type == fund_type)

    result = await db.execute(query)
    rankings = result.scalars().all()

    # 转换为字典列表
    fund_rankings = [
        {
            "code": r.code,
            "rank_3m": r.rank_3m or 0,
            "rank_6m": r.rank_6m or 0,
            "rank_1y": r.rank_1y or 0,
            "rank_3y": r.rank_3y or 0,
            "total_count": r.total_count or 1,
        }
        for r in rankings
    ]

    # 执行 4433 筛选
    screened = screen_funds_4433(fund_rankings)

    # 获取基金详情
    codes = [f["code"] for f in screened]
    funds_result = await db.execute(select(Fund).where(Fund.code.in_(codes)))
    funds_map = {f.code: f for f in funds_result.scalars().all()}

    # 合并数据
    data = []
    for item in screened:
        fund = funds_map.get(item["code"])
        if fund:
            data.append({
                "code": item["code"],
                "name": fund.name,
                "type": fund.type,
                "company": fund.company,
                "manager": fund.manager,
                "score_4433": item["score_4433"],
                "pct_3m": item["pct_3m"],
                "pct_6m": item["pct_6m"],
                "pct_1y": item["pct_1y"],
                "pct_3y": item["pct_3y"],
            })

    # 分页
    total = len(data)
    start = (page - 1) * size
    end = start + size
    paged = data[start:end]

    await cache_set(cache_key, {"items": paged, "total": total}, ttl=600)
    return {"data": {"items": paged, "total": total}, "page": page, "size": size}


@router.post("/check")
async def check_fund_4433(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """检查单个基金是否通过 4433"""
    result = await db.execute(
        select(FundRanking)
        .where(FundRanking.code == code)
        .order_by(FundRanking.rank_date.desc())
        .limit(1)
    )
    ranking = result.scalar_one_or_none()

    if not ranking:
        return {"error": "未找到该基金排名数据"}

    score = calculate_4433_score(
        rank_3m=ranking.rank_3m or 0,
        total_3m=ranking.total_count or 1,
        rank_6m=ranking.rank_6m or 0,
        total_6m=ranking.total_count or 1,
        rank_1y=ranking.rank_1y or 0,
        total_1y=ranking.total_count or 1,
        rank_3y=ranking.rank_3y or 0,
        total_3y=ranking.total_count or 1,
    )

    return {"data": {"code": code, **score}}


# 需要导入 func
from sqlalchemy import func
