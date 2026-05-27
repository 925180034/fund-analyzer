from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
from typing import Optional
import logging

from backend.database import get_db
from backend.models.user import UserFund
from backend.models.fund import Fund
from backend.models.nav import NavHistory
from backend.services.cache_manager import cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["持仓监控"])


@router.post("/add")
async def add_holding(
    fund_code: str = Body(..., embed=True, alias="code"),
    action: str = Body("持有", embed=True),
    buy_price: Optional[float] = Body(None, embed=True),
    buy_date: Optional[str] = Body(None, embed=True),
    amount: Optional[float] = Body(None, embed=True),
    user_id: str = Body("default", embed=True),
    db: AsyncSession = Depends(get_db),
):
    """添加持仓记录"""
    # 验证基金是否存在
    result = await db.execute(select(Fund).where(Fund.code == fund_code))
    fund = result.scalar_one_or_none()
    if not fund:
        return {"error": f"基金 {fund_code} 不存在"}

    parsed_date = None
    if buy_date:
        try:
            parsed_date = datetime.strptime(buy_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "日期格式错误，请使用 YYYY-MM-DD"}

    user_fund = UserFund(
        user_id=user_id,
        fund_code=fund_code,
        action=action,
        buy_price=buy_price,
        buy_date=parsed_date,
        amount=amount,
    )
    db.add(user_fund)
    await db.commit()
    await db.refresh(user_fund)

    return {
        "message": "持仓添加成功",
        "data": {
            "id": user_fund.id,
            "fund_code": fund_code,
            "fund_name": fund.name,
            "action": action,
            "buy_price": buy_price,
            "buy_date": str(buy_date),
            "amount": amount,
        },
    }


@router.get("/holdings")
async def get_holdings(
    user_id: str = Query("default"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有持仓"""
    result = await db.execute(
        select(UserFund).where(UserFund.user_id == user_id).order_by(UserFund.created_at.desc())
    )
    holdings = result.scalars().all()

    data = []
    for h in holdings:
        # 获取基金名称和最新净值
        fund_result = await db.execute(select(Fund).where(Fund.code == h.fund_code))
        fund = fund_result.scalar_one_or_none()

        nav_result = await db.execute(
            select(NavHistory)
            .where(NavHistory.code == h.fund_code)
            .order_by(NavHistory.date.desc())
            .limit(1)
        )
        latest_nav = nav_result.scalar_one_or_none()

        current_nav = latest_nav.nav if latest_nav else None
        profit_rate = None
        if h.buy_price and current_nav and h.buy_price > 0:
            profit_rate = round((current_nav - h.buy_price) / h.buy_price * 100, 2)

        profit_amount = None
        if h.amount and current_nav and h.buy_price:
            profit_amount = round((current_nav - h.buy_price) * h.amount, 2)

        data.append({
            "id": h.id,
            "fund_code": h.fund_code,
            "fund_name": fund.name if fund else None,
            "action": h.action,
            "buy_price": h.buy_price,
            "buy_date": str(h.buy_date) if h.buy_date else None,
            "amount": h.amount,
            "current_nav": current_nav,
            "profit_rate": profit_rate,
            "profit_amount": profit_amount,
            "created_at": str(h.created_at) if h.created_at else None,
        })

    return {"data": data}


@router.get("/alerts")
async def get_alerts(
    user_id: str = Query("default"),
    db: AsyncSession = Depends(get_db),
):
    """获取风险提醒"""
    result = await db.execute(
        select(UserFund).where(UserFund.user_id == user_id, UserFund.action == "持有")
    )
    holdings = result.scalars().all()

    alerts = []
    for h in holdings:
        # 获取最新净值
        nav_result = await db.execute(
            select(NavHistory)
            .where(NavHistory.code == h.fund_code)
            .order_by(NavHistory.date.desc())
            .limit(1)
        )
        latest_nav = nav_result.scalar_one_or_none()
        if not latest_nav:
            continue

        current_nav = latest_nav.nav

        # 获取基金信息
        fund_result = await db.execute(select(Fund).where(Fund.code == h.fund_code))
        fund = fund_result.scalar_one_or_none()
        fund_name = fund.name if fund else h.fund_code

        # 获取净值历史用于计算回撤
        nav_history_result = await db.execute(
            select(NavHistory)
            .where(NavHistory.code == h.fund_code)
            .order_by(NavHistory.date.desc())
            .limit(60)
        )
        nav_list = nav_history_result.scalars().all()

        if len(nav_list) >= 2:
            nav_values = [n.nav for n in reversed(nav_list)]
            peak = max(nav_values)
            drawdown = (current_nav - peak) / peak * 100 if peak > 0 else 0

            # 回撤超过10%提醒
            if drawdown < -10:
                alerts.append({
                    "fund_code": h.fund_code,
                    "fund_name": fund_name,
                    "type": "回撤警告",
                    "level": "warning" if drawdown > -20 else "danger",
                    "message": f"{fund_name}({h.fund_code}) 近期回撤 {drawdown:.1f}%，请关注",
                    "current_nav": current_nav,
                    "peak_nav": peak,
                    "drawdown": round(drawdown, 2),
                })

            # 连续下跌3天以上提醒
            recent_growth = [n.growth for n in nav_list[:5] if n.growth is not None]
            if len(recent_growth) >= 3 and all(g < 0 for g in recent_growth[:3]):
                alerts.append({
                    "fund_code": h.fund_code,
                    "fund_name": fund_name,
                    "type": "连续下跌",
                    "level": "warning",
                    "message": f"{fund_name}({h.fund_code}) 连续{len(recent_growth)}天下跌，建议关注",
                    "recent_growth": recent_growth[:5],
                })

        # 买入价格比较
        if h.buy_price and current_nav:
            change = (current_nav - h.buy_price) / h.buy_price * 100
            if change < -15:
                alerts.append({
                    "fund_code": h.fund_code,
                    "fund_name": fund_name,
                    "type": "亏损提醒",
                    "level": "danger",
                    "message": f"{fund_name}({h.fund_code}) 相比买入价亏损 {abs(change):.1f}%",
                    "buy_price": h.buy_price,
                    "current_nav": current_nav,
                    "change": round(change, 2),
                })

    # 按严重程度排序
    level_order = {"danger": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda x: level_order.get(x.get("level", "info"), 3))

    return {"data": alerts, "total": len(alerts)}
