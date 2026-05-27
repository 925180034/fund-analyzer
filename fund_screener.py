"""
基金筛选模块 - 4433法则 + 风险指标
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_4433_score(row):
    """
    4433法则评分
    - 4：近1年排名前1/4
    - 4：近2/3/5年排名前1/4
    - 3：近6月排名前1/3
    - 3：近3月排名前1/3
    """
    score = 0
    
    # 近1年排名前1/4
    if pd.notna(row.get('year_growth')) and row['year_growth'] > 0:
        score += 25
    
    # 近3年排名前1/4
    if pd.notna(row.get('three_year_growth')) and row['three_year_growth'] > 0:
        score += 25
    
    # 近6月排名前1/3
    if pd.notna(row.get('six_month_growth')) and row['six_month_growth'] > 0:
        score += 25
    
    # 近3月排名前1/3
    if pd.notna(row.get('three_month_growth')) and row['three_month_growth'] > 0:
        score += 25
    
    return score

def calculate_risk_metrics(nav_series, dates=None):
    """
    计算风险指标
    - 最大回撤
    - 年化收益率
    - 夏普比率
    - 波动率
    
    参数:
        nav_series: 净值序列
        dates: 日期序列（可选，用于计算天数）
    """
    if len(nav_series) < 2:
        return {}
    
    # 计算日收益率
    returns = nav_series.pct_change().dropna()
    
    # 计算总天数
    if dates is not None and len(dates) >= 2:
        try:
            total_days = (dates.iloc[-1] - dates.iloc[0]).days
        except:
            total_days = len(nav_series)
    else:
        total_days = len(nav_series)
    
    # 年化收益率
    total_return = (nav_series.iloc[-1] / nav_series.iloc[0]) - 1
    annual_return = (1 + total_return) ** (365 / total_days) - 1 if total_days > 0 else 0
    
    # 波动率（年化）
    volatility = returns.std() * np.sqrt(252)
    
    # 夏普比率（假设无风险利率2%）
    risk_free_rate = 0.02
    sharpe = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    # 最大回撤
    cummax = nav_series.cummax()
    drawdown = (nav_series - cummax) / cummax
    max_drawdown = drawdown.min()
    
    return {
        'total_return': round(total_return * 100, 2),
        'annual_return': round(annual_return * 100, 2),
        'volatility': round(volatility * 100, 2),
        'sharpe': round(sharpe, 2),
        'max_drawdown': round(max_drawdown * 100, 2),
        'total_days': total_days
    }

def screen_funds_4433(funds_df, min_score=75):
    """
    4433法则筛选基金
    """
    if funds_df.empty:
        return pd.DataFrame()
    
    funds_df['score_4433'] = funds_df.apply(calculate_4433_score, axis=1)
    filtered = funds_df[funds_df['score_4433'] >= min_score].copy()
    filtered = filtered.sort_values(['score_4433', 'year_growth'], ascending=[False, False])
    
    return filtered

def screen_funds_advanced(funds_df, filters=None):
    """
    高级筛选
    """
    if filters is None:
        filters = {}
    
    filtered = funds_df.copy()
    
    if filters.get('fund_type'):
        filtered = filtered[filtered['type'] == filters['fund_type']]
    
    if filters.get('min_year_return'):
        filtered = filtered[filtered['year_growth'] >= filters['min_year_return']]
    
    if filters.get('min_scale'):
        filtered = filtered[filtered['scale'] >= filters['min_scale']]
    
    if filters.get('max_fee'):
        filtered = filtered[filtered['fee_rate'] <= filters['max_fee']]
    
    return filtered

def compare_funds(fund_codes, nav_data_dict):
    """
    基金对比分析
    """
    comparison = {}
    
    for code in fund_codes:
        if code not in nav_data_dict:
            continue
        
        nav_df = nav_data_dict[code]
        if nav_df.empty:
            continue
        
        metrics = calculate_risk_metrics(nav_df['nav'], nav_df['date'])
        comparison[code] = metrics
    
    return comparison

def rank_funds(funds_df, weights=None):
    """
    基金综合排名
    """
    if weights is None:
        weights = {
            'return_weight': 0.4,
            'risk_weight': 0.3,
            'sharpe_weight': 0.3
        }
    
    df = funds_df.copy()
    
    # 归一化处理
    for col in ['year_growth', 'sharpe', 'max_drawdown']:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:
                df[f'{col}_norm'] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[f'{col}_norm'] = 0.5
    
    # 计算综合得分
    df['total_score'] = (
        df.get('year_growth_norm', 0) * weights['return_weight'] +
        (1 - df.get('max_drawdown_norm', 0)) * weights['risk_weight'] +
        df.get('sharpe_norm', 0) * weights['sharpe_weight']
    )
    
    return df.sort_values('total_score', ascending=False)
