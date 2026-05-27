"""
基金数据获取模块 - 基于 AKShare
"""
import akshare as ak
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'fund.db')

def get_db():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS funds (
            code TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            nav REAL,
            nav_date TEXT,
            day_growth REAL,
            year_growth REAL,
            manager TEXT,
            scale REAL,
            updated_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS nav_history (
            code TEXT,
            date TEXT,
            nav REAL,
            growth REAL,
            PRIMARY KEY (code, date)
        );
        
        CREATE TABLE IF NOT EXISTS favorites (
            code TEXT PRIMARY KEY,
            name TEXT,
            added_at TEXT
        );
    ''')
    conn.commit()
    conn.close()

def fetch_fund_ranking(fund_type="全部"):
    """获取基金排行"""
    try:
        df = ak.fund_open_fund_rank_em(symbol=fund_type)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"获取基金排行失败: {e}")
    return pd.DataFrame()

def fetch_fund_nav(code, start_date=None, end_date=None):
    """获取基金净值历史数据"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            df.columns = ['date', 'nav', 'growth']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            if start_date:
                df = df[df['date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['date'] <= pd.to_datetime(end_date)]
            
            return df
    except Exception as e:
        print(f"获取基金 {code} 净值失败: {e}")
    return pd.DataFrame()

def fetch_fund_info(code):
    """获取基金基本信息"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="基金概况")
        if df is not None and not df.empty:
            info = {}
            for _, row in df.iterrows():
                info[row.iloc[0]] = row.iloc[1]
            return info
    except Exception as e:
        print(f"获取基金 {code} 信息失败: {e}")
    return {}

def search_fund(keyword):
    """搜索基金"""
    try:
        df = fetch_fund_ranking("全部")
        if df is not None and not df.empty:
            mask = df['基金简称'].str.contains(keyword, na=False) | df['基金代码'].str.contains(keyword, na=False)
            return df[mask].head(20)
    except Exception as e:
        print(f"搜索基金失败: {e}")
    return pd.DataFrame()

def get_fund_types():
    """获取基金类型列表"""
    return ["全部", "股票型", "混合型", "债券型", "指数型", "QDII", "FOF"]

# 初始化数据库
init_db()
