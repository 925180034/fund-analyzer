from typing import List, Dict, Optional
from datetime import date
import numpy as np
import logging

logger = logging.getLogger(__name__)


def backtest_regular_invest(
    nav_data: List[Dict],
    invest_amount: float = 1000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    普通定投回测
    
    Args:
        nav_data: 净值数据列表 [{"date": "2020-01-01", "nav": 1.0}, ...]
        invest_amount: 每期定投金额
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        回测结果
    """
    if not nav_data:
        return {"error": "无净值数据"}

    # 按日期排序
    nav_data = sorted(nav_data, key=lambda x: x["date"])

    total_shares = 0.0
    total_invested = 0.0
    invest_count = 0
    records = []

    for item in nav_data:
        nav = item["nav"]
        if nav <= 0:
            continue

        shares = invest_amount / nav
        total_shares += shares
        total_invested += invest_amount
        invest_count += 1

        current_value = total_shares * nav
        profit = current_value - total_invested
        profit_rate = profit / total_invested if total_invested > 0 else 0

        records.append({
            "date": item["date"],
            "nav": nav,
            "shares": round(shares, 2),
            "total_shares": round(total_shares, 2),
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "profit": round(profit, 2),
            "profit_rate": round(profit_rate * 100, 2),
        })

    if not records:
        return {"error": "无有效回测数据"}

    last = records[-1]
    return {
        "strategy": "普通定投",
        "invest_amount": invest_amount,
        "invest_count": invest_count,
        "total_invested": last["total_invested"],
        "final_value": last["current_value"],
        "total_profit": last["profit"],
        "total_return": last["profit_rate"],
        "records": records,
    }


def backtest_smart_invest_ma(
    nav_data: List[Dict],
    invest_amount: float = 1000.0,
    ma_period: int = 250,
) -> Dict:
    """
    均线智能定投回测
    
    当净值低于均线时加大投入，高于均线时减少投入
    
    Args:
        nav_data: 净值数据
        invest_amount: 基准定投金额
        ma_period: 均线周期（默认250日）
    """
    if not nav_data:
        return {"error": "无净值数据"}

    nav_data = sorted(nav_data, key=lambda x: x["date"])
    nav_values = [item["nav"] for item in nav_data]

    total_shares = 0.0
    total_invested = 0.0
    invest_count = 0
    records = []

    for i, item in enumerate(nav_data):
        nav = item["nav"]
        if nav <= 0:
            continue

        # 计算均线
        if i >= ma_period:
            ma = np.mean(nav_values[i - ma_period:i])
            deviation = (nav - ma) / ma  # 偏离度

            # 根据偏离度调整投入金额
            # 偏离度 < -20%: 投入 2 倍
            # 偏离度 -20% ~ -10%: 投入 1.5 倍
            # 偏离度 -10% ~ 10%: 投入 1 倍
            # 偏离度 10% ~ 20%: 投入 0.5 倍
            # 偏离度 > 20%: 投入 0.3 倍
            if deviation < -0.2:
                ratio = 2.0
            elif deviation < -0.1:
                ratio = 1.5
            elif deviation < 0.1:
                ratio = 1.0
            elif deviation < 0.2:
                ratio = 0.5
            else:
                ratio = 0.3

            actual_amount = invest_amount * ratio
        else:
            actual_amount = invest_amount
            deviation = 0
            ratio = 1.0

        shares = actual_amount / nav
        total_shares += shares
        total_invested += actual_amount
        invest_count += 1

        current_value = total_shares * nav
        profit = current_value - total_invested
        profit_rate = profit / total_invested if total_invested > 0 else 0

        records.append({
            "date": item["date"],
            "nav": nav,
            "invest_amount": round(actual_amount, 2),
            "ratio": ratio,
            "deviation": round(deviation * 100, 2) if i >= ma_period else None,
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "profit": round(profit, 2),
            "profit_rate": round(profit_rate * 100, 2),
        })

    if not records:
        return {"error": "无有效回测数据"}

    last = records[-1]
    return {
        "strategy": "均线智能定投",
        "invest_amount": invest_amount,
        "ma_period": ma_period,
        "invest_count": invest_count,
        "total_invested": last["total_invested"],
        "final_value": last["current_value"],
        "total_profit": last["profit"],
        "total_return": last["profit_rate"],
        "records": records,
    }


def backtest_drawdown_invest(
    nav_data: List[Dict],
    invest_amount: float = 1000.0,
    drawdown_threshold: float = -0.1,
    extra_ratio: float = 2.0,
) -> Dict:
    """
    回撤加仓定投回测
    
    正常定投 + 当回撤超过阈值时额外加仓
    
    Args:
        nav_data: 净值数据
        invest_amount: 基准定投金额
        drawdown_threshold: 回撤触发阈值（如 -0.1 表示回撤10%触发）
        extra_ratio: 加仓倍数
    """
    if not nav_data:
        return {"error": "无净值数据"}

    nav_data = sorted(nav_data, key=lambda x: x["date"])
    nav_values = [item["nav"] for item in nav_data]

    total_shares = 0.0
    total_invested = 0.0
    invest_count = 0
    extra_count = 0
    peak = 0
    records = []

    for i, item in enumerate(nav_data):
        nav = item["nav"]
        if nav <= 0:
            continue

        # 更新峰值
        peak = max(peak, nav)
        drawdown = (nav - peak) / peak if peak > 0 else 0

        # 基础定投
        actual_amount = invest_amount

        # 回撤加仓逻辑
        if drawdown <= drawdown_threshold:
            extra_amount = invest_amount * extra_ratio
            actual_amount += extra_amount
            extra_count += 1

        shares = actual_amount / nav
        total_shares += shares
        total_invested += actual_amount
        invest_count += 1

        current_value = total_shares * nav
        profit = current_value - total_invested
        profit_rate = profit / total_invested if total_invested > 0 else 0

        records.append({
            "date": item["date"],
            "nav": nav,
            "drawdown": round(drawdown * 100, 2),
            "invest_amount": round(actual_amount, 2),
            "is_extra": drawdown <= drawdown_threshold,
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "profit": round(profit, 2),
            "profit_rate": round(profit_rate * 100, 2),
        })

    if not records:
        return {"error": "无有效回测数据"}

    last = records[-1]
    return {
        "strategy": "回撤加仓定投",
        "invest_amount": invest_amount,
        "drawdown_threshold": drawdown_threshold,
        "extra_ratio": extra_ratio,
        "invest_count": invest_count,
        "extra_count": extra_count,
        "total_invested": last["total_invested"],
        "final_value": last["current_value"],
        "total_profit": last["profit"],
        "total_return": last["profit_rate"],
        "records": records,
    }
