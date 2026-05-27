"""
定投回测模块
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def backtest_fixed_investment(nav_df, amount=1000, frequency='monthly', start_date=None, end_date=None):
    """
    定投回测
    
    参数:
        nav_df: 净值数据 DataFrame (columns: date, nav)
        amount: 每次定投金额
        frequency: 定投频率 ('weekly', 'biweekly', 'monthly')
        start_date: 开始日期
        end_date: 结束日期
    
    返回:
        回测结果字典
    """
    if nav_df.empty:
        return {}
    
    df = nav_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    
    if df.empty:
        return {}
    
    # 确定定投日期
    if frequency == 'weekly':
        # 每周一
        invest_dates = df[df['date'].dt.weekday == 0]['date'].tolist()
    elif frequency == 'biweekly':
        # 每两周的周一
        weekly_dates = df[df['date'].dt.weekday == 0]['date'].tolist()
        invest_dates = weekly_dates[::2]
    else:  # monthly
        # 每月第一个交易日
        df['year_month'] = df['date'].dt.to_period('M')
        invest_dates = df.groupby('year_month')['date'].first().tolist()
    
    if not invest_dates:
        return {}
    
    # 执行定投模拟
    total_invest = 0
    total_shares = 0
    invest_history = []
    value_history = []
    
    for invest_date in invest_dates:
        # 获取当天净值
        day_data = df[df['date'] == invest_date]
        if day_data.empty:
            continue
        
        nav = day_data['nav'].iloc[0]
        
        # 计算购买份额
        shares = amount / nav
        total_invest += amount
        total_shares += shares
        
        # 记录投资历史
        invest_history.append({
            'date': invest_date,
            'nav': nav,
            'amount': amount,
            'shares': shares,
            'total_invest': total_invest,
            'total_shares': total_shares,
            'total_value': total_shares * nav
        })
    
    if not invest_history:
        return {}
    
    # 计算每日资产价值
    for _, row in df.iterrows():
        current_value = total_shares * row['nav']
        value_history.append({
            'date': row['date'],
            'nav': row['nav'],
            'value': current_value,
            'invest': total_invest,
            'profit': current_value - total_invest,
            'return': (current_value / total_invest - 1) * 100 if total_invest > 0 else 0
        })
    
    # 计算风险指标
    value_series = pd.Series([v['value'] for v in value_history])
    returns = value_series.pct_change().dropna()
    
    # 最大回撤
    cummax = value_series.cummax()
    drawdown = (value_series - cummax) / cummax
    max_drawdown = drawdown.min() * 100
    
    # 年化收益率
    total_days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
    total_return = (total_shares * df['nav'].iloc[-1] / total_invest - 1) * 100
    annual_return = ((1 + total_return/100) ** (365/total_days) - 1) * 100 if total_days > 0 else 0
    
    # 夏普比率
    volatility = returns.std() * np.sqrt(252) * 100
    risk_free_rate = 2.0  # 无风险利率2%
    sharpe = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    # 最终结果
    final_value = total_shares * df['nav'].iloc[-1]
    
    return {
        'summary': {
            'total_invest': round(total_invest, 2),
            'final_value': round(final_value, 2),
            'total_profit': round(final_value - total_invest, 2),
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe': round(sharpe, 2),
            'volatility': round(volatility, 2),
            'invest_count': len(invest_history),
            'start_date': df['date'].iloc[0].strftime('%Y-%m-%d'),
            'end_date': df['date'].iloc[-1].strftime('%Y-%m-%d'),
            'total_days': total_days
        },
        'invest_history': invest_history,
        'value_history': value_history
    }

def backtest_smart_investment(nav_df, base_amount=1000, frequency='monthly', 
                               low_threshold=0.8, high_threshold=1.2):
    """
    智能定投回测（低估多投，高估少投）
    
    参数:
        nav_df: 净值数据
        base_amount: 基础定投金额
        frequency: 定投频率
        low_threshold: 低估阈值（相对均线）
        high_threshold: 高估阈值（相对均线）
    """
    if nav_df.empty:
        return {}
    
    df = nav_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 计算20日均线
    df['ma20'] = df['nav'].rolling(window=20).mean()
    df = df.dropna(subset=['ma20'])
    
    # 确定定投日期
    if frequency == 'weekly':
        invest_dates = df[df['date'].dt.weekday == 0]['date'].tolist()
    elif frequency == 'biweekly':
        weekly_dates = df[df['date'].dt.weekday == 0]['date'].tolist()
        invest_dates = weekly_dates[::2]
    else:  # monthly
        df['year_month'] = df['date'].dt.to_period('M')
        invest_dates = df.groupby('year_month')['date'].first().tolist()
    
    if not invest_dates:
        return {}
    
    # 执行智能定投
    total_invest = 0
    total_shares = 0
    invest_history = []
    
    for invest_date in invest_dates:
        day_data = df[df['date'] == invest_date]
        if day_data.empty:
            continue
        
        nav = day_data['nav'].iloc[0]
        ma20 = day_data['ma20'].iloc[0]
        
        # 计算相对均线位置
        ratio = nav / ma20
        
        # 智能调整金额
        if ratio < low_threshold:
            # 低估：多投
            amount = base_amount * 1.5
        elif ratio > high_threshold:
            # 高估：少投
            amount = base_amount * 0.5
        else:
            # 正常：基础金额
            amount = base_amount
        
        shares = amount / nav
        total_invest += amount
        total_shares += shares
        
        invest_history.append({
            'date': invest_date,
            'nav': nav,
            'ma20': ma20,
            'ratio': round(ratio, 2),
            'amount': round(amount, 2),
            'shares': shares,
            'total_invest': total_invest,
            'total_value': total_shares * nav
        })
    
    if not invest_history:
        return {}
    
    # 计算最终结果
    final_nav = df['nav'].iloc[-1]
    final_value = total_shares * final_nav
    total_return = (final_value / total_invest - 1) * 100
    
    total_days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
    annual_return = ((1 + total_return/100) ** (365/total_days) - 1) * 100 if total_days > 0 else 0
    
    return {
        'summary': {
            'total_invest': round(total_invest, 2),
            'final_value': round(final_value, 2),
            'total_profit': round(final_value - total_invest, 2),
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'invest_count': len(invest_history),
            'start_date': df['date'].iloc[0].strftime('%Y-%m-%d'),
            'end_date': df['date'].iloc[-1].strftime('%Y-%m-%d'),
            'strategy': 'smart'
        },
        'invest_history': invest_history
    }

def compare_strategies(nav_df, amount=1000):
    """
    对比不同定投策略
    """
    results = {}
    
    # 普通定投（每月）
    results['monthly'] = backtest_fixed_investment(nav_df, amount, 'monthly')
    
    # 普通定投（每周）
    results['weekly'] = backtest_fixed_investment(nav_df, amount, 'weekly')
    
    # 智能定投
    results['smart'] = backtest_smart_investment(nav_df, amount, 'monthly')
    
    return results
