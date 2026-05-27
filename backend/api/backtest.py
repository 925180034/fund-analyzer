from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from backend.database import get_db
from backend.models import NavHistory
from backend.services.backtester import (
    backtest_regular_invest,
    backtest_smart_invest_ma,
    backtest_drawdown_invest,
)
from backend.services.cache_manager import cache_get, cache_set

router = APIRouter(prefix="/backtest", tags=["回测"])


@router.get("/regular")
async def backtest_regular(
    code: str = Query(..., description="基金代码"),
    amount: float = Query(1000, description="每期定投金额"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
):
    """普通定投回测"""
    cache_key = f"backtest:regular:{code}:{amount}:{start_date}:{end_date}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    # 获取净值数据
    query = select(NavHistory).where(NavHistory.code == code)
    if start_date:
        query = query.where(NavHistory.date >= start_date)
    if end_date:
        query = query.where(NavHistory.date <= end_date)
    query = query.order_by(NavHistory.date.asc())

    result = await db.execute(query)
    nav_list = result.scalars().all()

    nav_data = [
        {"date": str(n.date), "nav": n.nav}
        for n in nav_list
        if n.nav and n.nav > 0
    ]

    if not nav_data:
        return {"error": "无净值数据"}

    backtest_result = backtest_regular_invest(nav_data, amount)
    await cache_set(cache_key, backtest_result, ttl=3600)
    return {"data": backtest_result}


@router.get("/smart-ma")
async def backtest_smart_ma(
    code: str = Query(..., description="基金代码"),
    amount: float = Query(1000, description="基准定投金额"),
    ma_period: int = Query(250, description="均线周期"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """均线智能定投回测"""
    cache_key = f"backtest:smart-ma:{code}:{amount}:{ma_period}:{start_date}:{end_date}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    query = select(NavHistory).where(NavHistory.code == code)
    if start_date:
        query = query.where(NavHistory.date >= start_date)
    if end_date:
        query = query.where(NavHistory.date <= end_date)
    query = query.order_by(NavHistory.date.asc())

    result = await db.execute(query)
    nav_list = result.scalars().all()

    nav_data = [
        {"date": str(n.date), "nav": n.nav}
        for n in nav_list
        if n.nav and n.nav > 0
    ]

    if not nav_data:
        return {"error": "无净值数据"}

    backtest_result = backtest_smart_invest_ma(nav_data, amount, ma_period)
    await cache_set(cache_key, backtest_result, ttl=3600)
    return {"data": backtest_result}


@router.get("/drawdown")
async def backtest_drawdown(
    code: str = Query(..., description="基金代码"),
    amount: float = Query(1000, description="基准定投金额"),
    threshold: float = Query(-0.1, description="回撤触发阈值"),
    extra_ratio: float = Query(2.0, description="加仓倍数"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """回撤加仓定投回测"""
    cache_key = f"backtest:drawdown:{code}:{amount}:{threshold}:{extra_ratio}:{start_date}:{end_date}"
    cached = await cache_get(cache_key)
    if cached:
        return {"data": cached}

    query = select(NavHistory).where(NavHistory.code == code)
    if start_date:
        query = query.where(NavHistory.date >= start_date)
    if end_date:
        query = query.where(NavHistory.date <= end_date)
    query = query.order_by(NavHistory.date.asc())

    result = await db.execute(query)
    nav_list = result.scalars().all()

    nav_data = [
        {"date": str(n.date), "nav": n.nav}
        for n in nav_list
        if n.nav and n.nav > 0
    ]

    if not nav_data:
        return {"error": "无净值数据"}

    backtest_result = backtest_drawdown_invest(nav_data, amount, threshold, extra_ratio)
    await cache_set(cache_key, backtest_result, ttl=3600)
    return {"data": backtest_result}
