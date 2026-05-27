from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from backend.database import get_db
from backend.models import Fund, NavHistory, FundRanking
from backend.services.cache_manager import cache_get, cache_set
from backend.services.risk_analyzer import max_drawdown, sharpe_ratio, annual_return, volatility

router = APIRouter(prefix="/fund", tags=["基金"])


@router.get("/search")
async def search_funds(
    keyword: str = Query(..., description="搜索关键词（基金代码或名称）"),
    fund_type: Optional[str] = Query(None, description="基金类型"),
    db: AsyncSession = Depends(get_db),
):
    """搜索基金"""
    cache_key = f"fund:search:{keyword}:{fund_type}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    query = select(Fund).where(
        or_(Fund.code.contains(keyword), Fund.name.contains(keyword))
    )
    if fund_type:
        query = query.where(Fund.type == fund_type)

    result = await db.execute(query.limit(50))
    funds = result.scalars().all()

    data = [
        {
            "code": f.code,
            "name": f.name,
            "type": f.type,
            "company": f.company,
            "manager": f.manager,
            "scale": f.scale,
        }
        for f in funds
    ]

    await cache_set(cache_key, data, ttl=300)
    return {"data": data}


@router.get("/detail/{code}")
async def get_fund_detail(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """获取基金详情"""
    cache_key = f"fund:detail:{code}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    # 获取基本信息
    result = await db.execute(select(Fund).where(Fund.code == code))
    fund = result.scalar_one_or_none()
    if not fund:
        return {"error": "基金不存在"}

    # 获取最新净值
    nav_result = await db.execute(
        select(NavHistory)
        .where(NavHistory.code == code)
        .order_by(NavHistory.date.desc())
        .limit(1)
    )
    latest_nav = nav_result.scalar_one_or_none()

    # 获取排名
    rank_result = await db.execute(
        select(FundRanking)
        .where(FundRanking.code == code)
        .order_by(FundRanking.rank_date.desc())
        .limit(1)
    )
    ranking = rank_result.scalar_one_or_none()

    data = {
        "code": fund.code,
        "name": fund.name,
        "type": fund.type,
        "company": fund.company,
        "manager": fund.manager,
        "establish_date": str(fund.establish_date) if fund.establish_date else None,
        "scale": fund.scale,
        "fee_buy": fund.fee_buy,
        "fee_sell": fund.fee_sell,
        "fee_manage": fund.fee_manage,
        "latest_nav": {
            "date": str(latest_nav.date) if latest_nav else None,
            "nav": latest_nav.nav if latest_nav else None,
            "acc_nav": latest_nav.acc_nav if latest_nav else None,
            "growth": latest_nav.growth if latest_nav else None,
        },
        "ranking": {
            "rank_3m": ranking.rank_3m if ranking else None,
            "rank_6m": ranking.rank_6m if ranking else None,
            "rank_1y": ranking.rank_1y if ranking else None,
            "rank_3y": ranking.rank_3y if ranking else None,
        } if ranking else None,
    }

    await cache_set(cache_key, data, ttl=600)
    return {"data": data}


@router.get("/ranking")
async def get_fund_ranking(
    fund_type: str = Query("全部", description="基金类型"),
    sort_by: str = Query("rank_1y", description="排序字段"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取基金排行"""
    cache_key = f"fund:ranking:{fund_type}:{sort_by}:{page}:{size}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    query = select(FundRanking).where(FundRanking.type == fund_type)

    # 排序
    sort_column = getattr(FundRanking, sort_by, FundRanking.rank_1y)
    query = query.order_by(sort_column.asc())

    # 分页
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    rankings = result.scalars().all()

    data = [
        {
            "code": r.code,
            "rank_date": str(r.rank_date),
            "rank_3m": r.rank_3m,
            "rank_6m": r.rank_6m,
            "rank_1y": r.rank_1y,
            "rank_3y": r.rank_3y,
            "total_count": r.total_count,
        }
        for r in rankings
    ]

    await cache_set(cache_key, data, ttl=600)
    return {"data": data, "page": page, "size": size}


@router.get("/nav/{code}")
async def get_fund_nav(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取基金净值历史"""
    cache_key = f"fund:nav:{code}:{start_date}:{end_date}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    query = select(NavHistory).where(NavHistory.code == code)
    if start_date:
        query = query.where(NavHistory.date >= start_date)
    if end_date:
        query = query.where(NavHistory.date <= end_date)

    query = query.order_by(NavHistory.date.asc())
    result = await db.execute(query.limit(1000))
    nav_list = result.scalars().all()

    data = [
        {
            "date": str(n.date),
            "nav": n.nav,
            "acc_nav": n.acc_nav,
            "growth": n.growth,
        }
        for n in nav_list
    ]

    await cache_set(cache_key, data, ttl=600)
    return {"data": data}
