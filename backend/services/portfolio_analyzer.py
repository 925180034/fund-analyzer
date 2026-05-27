"""组合分析服务

计算加权收益、波动率、最大回撤、夏普比率，
各基金贡献分析，组合净值走势。
"""

from typing import List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from backend.models.nav import NavHistory
from backend.services.risk_analyzer import (
    annual_return,
    max_drawdown,
    sharpe_ratio,
    volatility,
)


async def _fetch_nav_series(
    db: AsyncSession, fund_code: str
) -> List[Dict[str, Any]]:
    """从数据库获取基金净值序列，返回按日期升序的列表。"""
    result = await db.execute(
        select(NavHistory)
        .where(NavHistory.code == fund_code)
        .order_by(NavHistory.date.asc())
    )
    rows = result.scalars().all()
    return [
        {"date": str(r.date), "nav": r.nav, "acc_nav": r.acc_nav, "growth": r.growth}
        for r in rows
    ]


def _nav_to_returns(nav_list: List[float]) -> List[float]:
    """净值序列 → 日收益率序列"""
    returns = []
    for i in range(1, len(nav_list)):
        if nav_list[i - 1] and nav_list[i - 1] != 0:
            returns.append(nav_list[i] / nav_list[i - 1] - 1)
    return returns


def _weighted_portfolio_nav(
    fund_navs: Dict[str, List[Dict]],
    holdings: List[Tuple[str, float]],
) -> List[Dict[str, Any]]:
    """按权重合并各基金净值，生成组合净值走势。

    采用公共日期交集、按权重加权每日收益后累计为净值。
    """
    # 按基金code: date -> nav
    date_nav_maps: Dict[str, Dict[str, float]] = {}
    for code, _ in holdings:
        series = fund_navs.get(code, [])
        date_nav_maps[code] = {r["date"]: r["nav"] for r in series if r["nav"]}

    # 公共日期交集
    date_sets = [set(dn.keys()) for dn in date_nav_maps.values()]
    if not date_sets or not date_sets[0]:
        return []
    common_dates = sorted(set.intersection(*date_sets))
    if len(common_dates) < 2:
        return []

    # 计算加权日收益
    normalized = [(w / 100.0) if w > 1 else w for _, w in holdings]
    weighted_returns = []
    for i in range(1, len(common_dates)):
        day_ret = 0.0
        for (code, _), w in zip(holdings, normalized):
            dn = date_nav_maps[code]
            prev_nav = dn[common_dates[i - 1]]
            cur_nav = dn[common_dates[i]]
            if prev_nav and prev_nav != 0:
                day_ret += w * (cur_nav / prev_nav - 1)
        weighted_returns.append(day_ret)

    # 累计净值
    portfolio_nav = [1.0]
    for r in weighted_returns:
        portfolio_nav.append(portfolio_nav[-1] * (1 + r))

    return [
        {"date": common_dates[i], "nav": round(portfolio_nav[i], 6)}
        for i in range(len(common_dates))
    ]


async def analyze_portfolio(
    db: AsyncSession,
    holdings: List[Tuple[str, float]],
) -> Dict[str, Any]:
    """主分析入口。

    Parameters
    ----------
    db : AsyncSession
    holdings : list of (fund_code, weight)

    Returns
    -------
    dict with keys:
        summary, fund_contributions, nav_series
    """
    if not holdings:
        return {
            "summary": {},
            "fund_contributions": [],
            "nav_series": [],
        }

    # 拉取各基金净值
    fund_navs: Dict[str, List[Dict]] = {}
    for code, _ in holdings:
        fund_navs[code] = await _fetch_nav_series(db, code)

    # 组合净值走势
    nav_series = _weighted_portfolio_nav(fund_navs, holdings)

    # 组合收益率序列
    nav_values = [p["nav"] for p in nav_series]
    portfolio_returns = _nav_to_returns(nav_values)

    # 组合指标
    summary = {
        "annual_return": round(annual_return(portfolio_returns) * 100, 2),
        "volatility": round(volatility(portfolio_returns) * 100, 2),
        "max_drawdown": round(max_drawdown(nav_values) * 100, 2),
        "sharpe_ratio": round(sharpe_ratio(portfolio_returns), 4),
        "total_return": round(
            ((nav_values[-1] / nav_values[0]) - 1) * 100, 2
        ) if len(nav_values) >= 2 else 0,
        "days": len(portfolio_returns),
    }

    # 各基金贡献分析
    normalized = [(w / 100.0) if w > 1 else w for _, w in holdings]
    fund_contributions = []
    for (code, weight), w in zip(holdings, normalized):
        series = fund_navs.get(code, [])
        f_navs = [r["nav"] for r in series if r["nav"]]
        f_returns = _nav_to_returns(f_navs)
        f_ann_ret = annual_return(f_returns)
        contribution = round(w * f_ann_ret * 100, 2)

        fund_contributions.append({
            "code": code,
            "weight": weight,
            "annual_return": round(f_ann_ret * 100, 2),
            "volatility": round(volatility(f_returns) * 100, 2),
            "max_drawdown": round(max_drawdown(f_navs) * 100, 2),
            "contribution": contribution,
        })

    return {
        "summary": summary,
        "fund_contributions": fund_contributions,
        "nav_series": nav_series,
    }
