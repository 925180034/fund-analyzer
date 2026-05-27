import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


def annual_return(returns: List[float], trading_days: int = 245) -> float:
    """计算年化收益率"""
    if not returns or len(returns) < 2:
        return 0.0
    total_return = np.prod([1 + r for r in returns]) - 1
    years = len(returns) / trading_days
    if years <= 0:
        return 0.0
    return (1 + total_return) ** (1 / years) - 1


def max_drawdown(nav_list: List[float]) -> float:
    """计算最大回撤"""
    if not nav_list or len(nav_list) < 2:
        return 0.0
    nav_array = np.array(nav_list)
    peak = np.maximum.accumulate(nav_array)
    drawdown = (nav_array - peak) / peak
    return float(np.min(drawdown))


def volatility(returns: List[float], trading_days: int = 245) -> float:
    """计算年化波动率"""
    if not returns or len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1) * np.sqrt(trading_days))


def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02, trading_days: int = 245) -> float:
    """计算夏普比率"""
    if not returns or len(returns) < 2:
        return 0.0
    ann_ret = annual_return(returns, trading_days)
    vol = volatility(returns, trading_days)
    if vol == 0:
        return 0.0
    return (ann_ret - risk_free_rate) / vol


def calmar_ratio(returns: List[float], trading_days: int = 245) -> float:
    """计算卡尔玛比率（年化收益/最大回撤）"""
    if not returns or len(returns) < 2:
        return 0.0
    ann_ret = annual_return(returns, trading_days)
    nav_list = [1.0]
    for r in returns:
        nav_list.append(nav_list[-1] * (1 + r))
    mdd = abs(max_drawdown(nav_list))
    if mdd == 0:
        return 0.0
    return ann_ret / mdd


def sortino_ratio(returns: List[float], risk_free_rate: float = 0.02, trading_days: int = 245) -> float:
    """计算索提诺比率（只考虑下行风险）"""
    if not returns or len(returns) < 2:
        return 0.0
    ann_ret = annual_return(returns, trading_days)
    downside_returns = [r for r in returns if r < 0]
    if not downside_returns:
        return float('inf') if ann_ret > risk_free_rate else 0.0
    downside_vol = float(np.std(downside_returns, ddof=1) * np.sqrt(trading_days))
    if downside_vol == 0:
        return 0.0
    return (ann_ret - risk_free_rate) / downside_vol


def win_rate(returns: List[float]) -> float:
    """计算胜率（正收益天数占比）"""
    if not returns:
        return 0.0
    positive_days = sum(1 for r in returns if r > 0)
    return positive_days / len(returns)
