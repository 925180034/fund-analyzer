import numpy as np
from typing import Optional
from datetime import date, timedelta
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models.fund import Fund
from backend.models.nav import NavHistory
from backend.models.ranking import FundRanking
from backend.services.risk_analyzer import (
    annual_return,
    max_drawdown,
    sharpe_ratio,
    volatility,
    calmar_ratio,
    sortino_ratio,
    win_rate,
)

logger = logging.getLogger(__name__)


async def generate_fund_report(code: str) -> dict:
    """生成基金诊断报告"""
    async with AsyncSessionLocal() as db:
        # 获取基金基本信息
        fund_result = await db.execute(select(Fund).where(Fund.code == code))
        fund = fund_result.scalar_one_or_none()
        if not fund:
            return {"error": f"基金 {code} 不存在"}

        # 获取净值历史（最近2年）
        two_years_ago = date.today() - timedelta(days=730)
        nav_result = await db.execute(
            select(NavHistory)
            .where(NavHistory.code == code, NavHistory.date >= two_years_ago)
            .order_by(NavHistory.date.asc())
        )
        nav_list = nav_result.scalars().all()

        if len(nav_list) < 30:
            return {"error": "净值数据不足，无法生成报告", "data_points": len(nav_list)}

        # 提取净值和收益率
        nav_values = [n.nav for n in nav_list if n.nav and n.nav > 0]
        dates = [n.date for n in nav_list if n.nav and n.nav > 0]
        growth_values = [n.growth / 100 for n in nav_list if n.growth is not None]

        if len(nav_values) < 30:
            return {"error": "有效净值数据不足"}

        # === 计算各指标 ===
        ann_ret = annual_return(growth_values)
        mdd = max_drawdown(nav_values)
        vol = volatility(growth_values)
        sr = sharpe_ratio(growth_values)
        cr = calmar_ratio(growth_values)
        sort_r = sortino_ratio(growth_values)
        wr = win_rate(growth_values)

        # 近期收益
        latest_nav = nav_values[-1]
        nav_1m_ago = nav_values[max(0, len(nav_values) - 22)]
        nav_3m_ago = nav_values[max(0, len(nav_values) - 66)]
        nav_6m_ago = nav_values[max(0, len(nav_values) - 132)]
        nav_1y_ago = nav_values[max(0, len(nav_values) - 245)]

        ret_1m = (latest_nav - nav_1m_ago) / nav_1m_ago * 100
        ret_3m = (latest_nav - nav_3m_ago) / nav_3m_ago * 100
        ret_6m = (latest_nav - nav_6m_ago) / nav_6m_ago * 100
        ret_1y = (latest_nav - nav_1y_ago) / nav_1y_ago * 100

        # 获取排名
        rank_result = await db.execute(
            select(FundRanking).where(FundRanking.code == code).order_by(FundRanking.rank_date.desc()).limit(1)
        )
        ranking = rank_result.scalar_one_or_none()

        # === 生成分析建议 ===
        suggestions = _generate_suggestions(
            ann_ret=ann_ret,
            mdd=mdd,
            sr=sr,
            vol=vol,
            cr=cr,
            wr=wr,
            ret_1m=ret_1m,
            ret_3m=ret_3m,
            fund_type=fund.type or "未知",
        )

        # === 评分 ===
        score = _calculate_score(ann_ret, mdd, sr, vol, wr)

        return {
            "code": code,
            "name": fund.name,
            "type": fund.type,
            "manager": fund.manager,
            "company": fund.company,
            "report_date": str(date.today()),
            "data_range": {
                "start": str(dates[0]),
                "end": str(dates[-1]),
                "data_points": len(nav_values),
            },
            "performance": {
                "latest_nav": latest_nav,
                "return_1m": round(ret_1m, 2),
                "return_3m": round(ret_3m, 2),
                "return_6m": round(ret_6m, 2),
                "return_1y": round(ret_1y, 2),
                "annual_return": round(ann_ret * 100, 2),
            },
            "risk": {
                "max_drawdown": round(mdd * 100, 2),
                "volatility": round(vol * 100, 2),
                "sharpe_ratio": round(sr, 2),
                "calmar_ratio": round(cr, 2),
                "sortino_ratio": round(sort_r, 2),
                "win_rate": round(wr * 100, 2),
            },
            "ranking": {
                "rank_3m": ranking.rank_3m if ranking else None,
                "rank_6m": ranking.rank_6m if ranking else None,
                "rank_1y": ranking.rank_1y if ranking else None,
                "total_count": ranking.total_count if ranking else None,
            } if ranking else None,
            "score": score,
            "suggestions": suggestions,
        }


def _calculate_score(ann_ret, mdd, sr, vol, wr) -> dict:
    """计算综合评分 (0-100)"""
    # 收益得分 (30分)
    ret_score = min(30, max(0, ann_ret * 100 * 3))

    # 风险得分 (30分) - 回撤越小越好
    risk_score = max(0, 30 + mdd * 100)  # mdd是负数

    # 夏普得分 (20分)
    sharpe_score = min(20, max(0, sr * 10))

    # 胜率得分 (20分)
    win_score = wr * 20

    total = round(ret_score + risk_score + sharpe_score + win_score, 1)
    total = max(0, min(100, total))

    if total >= 80:
        grade = "优秀"
    elif total >= 60:
        grade = "良好"
    elif total >= 40:
        grade = "一般"
    else:
        grade = "较差"

    return {
        "total": total,
        "grade": grade,
        "return_score": round(ret_score, 1),
        "risk_score": round(risk_score, 1),
        "sharpe_score": round(sharpe_score, 1),
        "win_score": round(win_score, 1),
    }


def _generate_suggestions(ann_ret, mdd, sr, vol, cr, wr, ret_1m, ret_3m, fund_type) -> list:
    """生成文字分析建议"""
    suggestions = []

    # 收益分析
    if ann_ret > 0.15:
        suggestions.append("📈 收益能力突出，年化收益率超过15%，表现优秀")
    elif ann_ret > 0.05:
        suggestions.append("📊 收益能力尚可，年化收益率在5%-15%之间")
    elif ann_ret > 0:
        suggestions.append("📉 收益能力一般，年化收益率低于5%，可考虑替换")
    else:
        suggestions.append("⚠️ 收益为负，建议重新评估投资策略")

    # 风险分析
    if mdd > -0.1:
        suggestions.append("🛡️ 风险控制良好，最大回撤小于10%，适合稳健型投资者")
    elif mdd > -0.2:
        suggestions.append("⚡ 风险适中，最大回撤10%-20%，需关注市场波动")
    elif mdd > -0.3:
        suggestions.append("🔴 风险偏高，最大回撤20%-30%，仅适合风险承受能力强的投资者")
    else:
        suggestions.append("🚨 风险过高，最大回撤超过30%，建议降低仓位或更换")

    # 夏普比率分析
    if sr > 2:
        suggestions.append("🏆 夏普比率优秀(>2)，风险调整后收益极佳")
    elif sr > 1:
        suggestions.append("✅ 夏普比率良好(>1)，性价比不错")
    elif sr > 0.5:
        suggestions.append("➖ 夏普比率一般(0.5-1)，风险收益匹配度中等")
    else:
        suggestions.append("⚠️ 夏普比率较低(<0.5)，承担的风险未获得合理补偿")

    # 近期趋势
    if ret_1m > 5:
        suggestions.append("📈 近1月涨幅较大(+{:.1f}%)，注意追高风险".format(ret_1m))
    elif ret_1m < -5:
        suggestions.append("📉 近1月跌幅较大({:.1f}%)，可考虑逢低加仓或止损".format(ret_1m))

    # 波动率分析
    if vol > 0.3:
        suggestions.append("🌊 波动率较高({:.0f}%)，净值波动大，定投策略可能更适合".format(vol * 100))
    elif vol < 0.1:
        suggestions.append("🎯 波动率较低({:.0f}%)，收益稳定，适合一次性投入".format(vol * 100))

    # 胜率分析
    if wr > 0.55:
        suggestions.append("🎯 日胜率{:.0f}%，上涨天数多于下跌天数".format(wr * 100))

    # 基金类型建议
    if "股票" in fund_type or "混合" in fund_type:
        suggestions.append("💡 建议持有期至少1年以上，避免频繁交易")
    elif "债券" in fund_type:
        suggestions.append("💡 债券型基金适合作为资产配置的稳定器")

    return suggestions
