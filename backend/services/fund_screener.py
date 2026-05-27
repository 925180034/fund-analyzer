from typing import List, Dict
from backend.services.risk_analyzer import (
    annual_return, max_drawdown, sharpe_ratio, volatility, calmar_ratio
)
import logging

logger = logging.getLogger(__name__)


def calculate_4433_score(
    rank_3m: int, total_3m: int,
    rank_6m: int, total_6m: int,
    rank_1y: int, total_1y: int,
    rank_3y: int, total_3y: int,
) -> dict:
    """
    4433 筛选法评分
    
    4: 近1年排名前 1/4
    4: 近2年、3年排名前 1/4  
    3: 近6月排名前 1/3
    3: 近3月排名前 1/3
    
    返回是否通过以及各项排名百分位
    """
    def rank_percentile(rank: int, total: int) -> float:
        if total <= 0 or rank <= 0:
            return 1.0
        return rank / total

    pct_3m = rank_percentile(rank_3m, total_3m)
    pct_6m = rank_percentile(rank_6m, total_6m)
    pct_1y = rank_percentile(rank_1y, total_1y)
    pct_3y = rank_percentile(rank_3y, total_3y)

    # 4433 条件
    cond_4_long = pct_1y <= 0.25       # 第一个4: 近1年
    cond_4_long2 = pct_3y <= 0.25      # 第二个4: 近3年
    cond_3_mid = pct_6m <= 1 / 3       # 第一个3: 近6月
    cond_3_short = pct_3m <= 1 / 3     # 第二个3: 近3月

    # 计算综合得分 (0-100)
    # 越低越好，所以用 1 - percentile
    score = (
        (1 - pct_3m) * 25 +
        (1 - pct_6m) * 25 +
        (1 - pct_1y) * 25 +
        (1 - pct_3y) * 25
    )

    passed = cond_4_long and cond_4_long2 and cond_3_mid and cond_3_short

    return {
        "passed": passed,
        "score": round(score, 2),
        "pct_3m": round(pct_3m * 100, 2),
        "pct_6m": round(pct_6m * 100, 2),
        "pct_1y": round(pct_1y * 100, 2),
        "pct_3y": round(pct_3y * 100, 2),
        "conditions": {
            "近1年前25%": cond_4_long,
            "近3年前25%": cond_4_long2,
            "近6月前33%": cond_3_mid,
            "近3月前33%": cond_3_short,
        }
    }


def screen_funds_4433(fund_rankings: List[Dict]) -> List[Dict]:
    """批量筛选基金，返回通过 4433 的基金列表"""
    results = []
    for fund in fund_rankings:
        score = calculate_4433_score(
            rank_3m=fund.get("rank_3m", 0),
            total_3m=fund.get("total_count", 1),
            rank_6m=fund.get("rank_6m", 0),
            total_6m=fund.get("total_count", 1),
            rank_1y=fund.get("rank_1y", 0),
            total_1y=fund.get("total_count", 1),
            rank_3y=fund.get("rank_3y", 0),
            total_3y=fund.get("total_count", 1),
        )
        if score["passed"]:
            results.append({
                **fund,
                "score_4433": score["score"],
                "pct_3m": score["pct_3m"],
                "pct_6m": score["pct_6m"],
                "pct_1y": score["pct_1y"],
                "pct_3y": score["pct_3y"],
            })

    # 按综合得分排序
    results.sort(key=lambda x: x["score_4433"], reverse=True)
    return results
