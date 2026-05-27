"""
基金分析平台 - Flask 后端
"""
from flask import Flask, render_template, jsonify, request
import akshare as ak
import pandas as pd
import json
from datetime import datetime, timedelta
from data_fetcher import fetch_fund_nav, fetch_fund_info, fetch_fund_ranking, search_fund
from fund_screener import screen_funds_4433, calculate_risk_metrics, compare_funds
from backtester import backtest_fixed_investment, backtest_smart_investment, compare_strategies

app = Flask(__name__)

# 缓存
cache = {}

def get_cached_data(key, fetch_fn, expire_hours=24):
    """简单缓存"""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < timedelta(hours=expire_hours):
            return data
    
    data = fetch_fn()
    cache[key] = (data, datetime.now())
    return data

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """搜索基金"""
    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400
    
    try:
        df = search_fund(keyword)
        if df.empty:
            return jsonify({'results': []})
        
        results = []
        for _, row in df.iterrows():
            results.append({
                'code': str(row.get('基金代码', '')),
                'name': str(row.get('基金简称', '')),
                'type': str(row.get('基金类型', '')),
                'nav': float(row.get('单位净值', 0)) if pd.notna(row.get('单位净值')) else 0,
                'day_growth': float(row.get('日增长率', 0)) if pd.notna(row.get('日增长率')) else 0
            })
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fund/<code>')
def api_fund_detail(code):
    """获取基金详情"""
    try:
        # 获取净值数据
        nav_df = fetch_fund_nav(code)
        if nav_df.empty:
            return jsonify({'error': '未找到基金数据'}), 404
        
        # 计算风险指标（传递日期列）
        metrics = calculate_risk_metrics(nav_df['nav'], nav_df['date'])
        
        # 获取基本信息
        info = fetch_fund_info(code)
        
        # 构建净值历史数据
        nav_history = []
        for _, row in nav_df.iterrows():
            nav_history.append({
                'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                'nav': round(float(row['nav']), 4),
                'growth': round(float(row.get('growth', 0)), 2) if pd.notna(row.get('growth')) else 0
            })
        
        return jsonify({
            'code': code,
            'info': info,
            'metrics': metrics,
            'nav_history': nav_history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/screen')
def api_screen():
    """基金筛选"""
    try:
        fund_type = request.args.get('type', '全部')
        min_return = float(request.args.get('min_return', 0))
        min_score = int(request.args.get('min_score', 50))
        
        # 获取基金排行
        df = fetch_fund_ranking(fund_type)
        if df.empty:
            return jsonify({'error': '获取基金数据失败'}), 500
        
        # 转换列名
        column_map = {
            '基金代码': 'code',
            '基金简称': 'name',
            '基金类型': 'type',
            '单位净值': 'nav',
            '日增长率': 'day_growth',
            '今年来': 'year_growth',
            '近1周': 'week_growth',
            '近1月': 'month_growth',
            '近3月': 'three_month_growth',
            '近6月': 'six_month_growth',
            '近1年': 'year_growth',
            '近3年': 'three_year_growth',
            '基金经理': 'manager',
            '基金规模(亿元)': 'scale'
        }
        
        df = df.rename(columns=column_map)
        
        # 筛选
        if min_return > 0:
            df = df[pd.to_numeric(df.get('year_growth', 0), errors='coerce') >= min_return]
        
        # 转换为列表
        results = []
        for _, row in df.head(50).iterrows():
            results.append({
                'code': str(row.get('code', '')),
                'name': str(row.get('name', '')),
                'type': str(row.get('type', '')),
                'nav': float(row.get('nav', 0)) if pd.notna(row.get('nav')) else 0,
                'day_growth': float(row.get('day_growth', 0)) if pd.notna(row.get('day_growth')) else 0,
                'week_growth': float(row.get('week_growth', 0)) if pd.notna(row.get('week_growth')) else 0,
                'month_growth': float(row.get('month_growth', 0)) if pd.notna(row.get('month_growth')) else 0,
                'year_growth': float(row.get('year_growth', 0)) if pd.notna(row.get('year_growth')) else 0,
                'manager': str(row.get('manager', '')),
                'scale': float(row.get('scale', 0)) if pd.notna(row.get('scale')) else 0
            })
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def api_backtest():
    """定投回测"""
    try:
        data = request.json
        code = data.get('code')
        amount = float(data.get('amount', 1000))
        frequency = data.get('frequency', 'monthly')
        strategy = data.get('strategy', 'fixed')
        start_date = data.get('start_date')
        
        if not code:
            return jsonify({'error': '请提供基金代码'}), 400
        
        # 获取净值数据
        nav_df = fetch_fund_nav(code, start_date)
        if nav_df.empty:
            return jsonify({'error': '获取基金数据失败'}), 500
        
        # 执行回测
        if strategy == 'smart':
            result = backtest_smart_investment(nav_df, amount, frequency)
        elif strategy == 'compare':
            result = compare_strategies(nav_df, amount)
        else:
            result = backtest_fixed_investment(nav_df, amount, frequency, start_date)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """基金对比"""
    try:
        data = request.json
        codes = data.get('codes', [])
        
        if len(codes) < 2:
            return jsonify({'error': '请选择至少2只基金'}), 400
        
        # 获取各基金数据
        nav_data = {}
        fund_info = {}
        
        for code in codes:
            nav_df = fetch_fund_nav(code)
            if not nav_df.empty:
                nav_data[code] = nav_df
                metrics = calculate_risk_metrics(nav_df['nav'], nav_df['date'])
                fund_info[code] = metrics
        
        return jsonify({
            'funds': fund_info,
            'nav_data': {code: df.to_dict(orient='records') for code, df in nav_data.items()}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ranking')
def api_ranking():
    """基金排行"""
    try:
        fund_type = request.args.get('type', '全部')
        df = fetch_fund_ranking(fund_type)
        
        if df.empty:
            return jsonify({'error': '获取排行失败'}), 500
        
        results = []
        for _, row in df.head(100).iterrows():
            results.append({
                'code': str(row.get('基金代码', '')),
                'name': str(row.get('基金简称', '')),
                'type': str(row.get('基金类型', '')),
                'nav': float(row.get('单位净值', 0)) if pd.notna(row.get('单位净值')) else 0,
                'day_growth': float(row.get('日增长率', 0)) if pd.notna(row.get('日增长率')) else 0,
                'year_growth': float(row.get('今年来', 0)) if pd.notna(row.get('今年来')) else 0,
                'manager': str(row.get('基金经理', '')),
                'scale': float(row.get('基金规模(亿元)', 0)) if pd.notna(row.get('基金规模(亿元)')) else 0
            })
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
