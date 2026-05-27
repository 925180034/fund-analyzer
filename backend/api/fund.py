from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models import Fund, NavHistory, FundRanking
from backend.services.cache_manager import cache_get, cache_set

router = APIRouter(prefix="/fund", tags=["基金"])


@router.get("/search")
async def search_funds(
    keyword: str = Query(..., description="搜索关键词"),
    fund_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """搜索基金"""
    query = select(Fund).where(
        or_(Fund.code.contains(keyword), Fund.name.contains(keyword))
    )
    if fund_type:
        query = query.where(Fund.type == fund_type)

    result = await db.execute(query.limit(50))
    funds = result.scalars().all()

    return {
        "data": [
            {"code": f.code, "name": f.name, "type": f.type, "company": f.company, "manager": f.manager, "scale": f.scale}
            for f in funds
        ]
    }


@router.get("/detail/{code}")
async def get_fund_detail(code: str, db: AsyncSession = Depends(get_db)):
    """获取基金详情（含净值历史和阶段收益）"""
    # 基本信息
    result = await db.execute(select(Fund).where(Fund.code == code))
    fund = result.scalar_one_or_none()
    if not fund:
        return {"error": "基金不存在"}

    # 净值历史
    nav_result = await db.execute(
        select(NavHistory).where(NavHistory.code == code).order_by(NavHistory.date.asc())
    )
    nav_list = nav_result.scalars().all()

    if not nav_list:
        return {"error": "无净值数据"}

    # 最新净值
    latest = nav_list[-1]
    prev = nav_list[-2] if len(nav_list) > 1 else latest
    change = round((float(latest.nav) - float(prev.nav)) / float(prev.nav) * 100, 2) if prev.nav else 0

    # 计算阶段收益
    now = datetime.now().date()
    def get_return(days):
        target_date = now - timedelta(days=days)
        for n in nav_list:
            if n.date >= target_date:
                start_nav = float(n.nav)
                end_nav = float(latest.nav)
                return round((end_nav - start_nav) / start_nav * 100, 2)
        return None

    # 净值历史数据
    nav_history = [{"date": str(n.date), "nav": float(n.nav)} for n in nav_list[-500:]]

    return {
        "code": fund.code,
        "name": fund.name,
        "type": fund.type,
        "company": fund.company,
        "manager": fund.manager,
        "nav": float(latest.nav),
        "change": change,
        "acc_nav": float(latest.acc_nav) if latest.acc_nav else None,
        "nav_date": str(latest.date),
        "month1": get_return(30),
        "month3": get_return(90),
        "month6": get_return(180),
        "year1": get_return(365),
        "year3": get_return(1095),
        "nav_history": nav_history,
    }


@router.get("/ranking")
async def get_fund_ranking(
    fund_type: str = Query("全部"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """基金排行"""
    query = select(Fund).where(Fund.type == fund_type) if fund_type != "全部" else select(Fund)
    query = query.order_by(Fund.scale.desc().nullslast())
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    funds = result.scalars().all()

    return {
        "data": [
            {"code": f.code, "name": f.name, "type": f.type, "manager": f.manager, "scale": f.scale}
            for f in funds
        ],
        "page": page,
        "size": size,
    }


@router.get("/nav/{code}")
async def get_fund_nav(code: str, db: AsyncSession = Depends(get_db)):
    """获取基金净值历史"""
    result = await db.execute(
        select(NavHistory).where(NavHistory.code == code).order_by(NavHistory.date.asc()).limit(1000)
    )
    nav_list = result.scalars().all()

    return {
        "data": [{"date": str(n.date), "nav": float(n.nav), "growth": float(n.growth) if n.growth else 0} for n in nav_list]
    }


@router.get("/manager/{manager_name}")
async def get_manager_analysis(manager_name: str, db: AsyncSession = Depends(get_db)):
    """基金经理分析"""
    result = await db.execute(select(Fund).where(Fund.manager.contains(manager_name)))
    funds = result.scalars().all()

    if not funds:
        return {"error": f"未找到基金经理: {manager_name}"}

    fund_list = []
    for f in funds:
        nav_result = await db.execute(
            select(NavHistory).where(NavHistory.code == f.code).order_by(NavHistory.date.desc()).limit(1)
        )
        latest_nav = nav_result.scalar_one_or_none()
        fund_list.append({
            "code": f.code,
            "name": f.name,
            "type": f.type,
            "scale": f.scale,
            "latest_nav": float(latest_nav.nav) if latest_nav else None,
        })

    return {
        "data": {
            "manager_name": manager_name,
            "fund_count": len(funds),
            "funds": fund_list,
        }
    }
