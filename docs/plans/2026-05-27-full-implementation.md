# 基金分析平台 — 完整实施计划

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** 完成三阶段全部功能：数据填充、组合管理、监控报告

**Architecture:** FastAPI + Vue3 + PostgreSQL + Redis 单体应用

---

## Batch 1: 数据填充 + 修复（紧急）

### Task 1.1: 填充基金数据到 PostgreSQL

**Files:**
- Create: `backend/scripts/seed_data.py`

**Step 1: 创建数据填充脚本**

```python
#!/usr/bin/env python3
"""填充基金基础数据到 PostgreSQL"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.database import async_session, init_db
from backend.models.fund import Fund
from backend.models.nav import NavHistory
from backend.services.data_fetcher import DataFetcher
from datetime import datetime

fetcher = DataFetcher()

async def seed_fund_list():
    """填充基金列表"""
    print("开始获取基金列表...")
    df = fetcher.fetch_fund_list("全部")
    if df.empty:
        print("获取基金列表失败")
        return
    
    async with async_session() as session:
        count = 0
        for _, row in df.iterrows():
            fund = Fund(
                code=str(row.get("基金代码", "")),
                name=str(row.get("基金简称", "")),
                type=str(row.get("基金类型", "")),
                manager=str(row.get("基金经理", "")),
                scale=float(row.get("基金规模(亿元)", 0) or 0),
                updated_at=datetime.now()
            )
            await session.merge(fund)
            count += 1
            if count % 100 == 0:
                print(f"  已处理 {count} 只基金...")
        await session.commit()
    print(f"基金列表填充完成，共 {count} 只")

async def seed_sample_nav():
    """为热门基金填充净值数据"""
    print("开始获取热门基金净值...")
    hot_funds = ["110011", "005827", "161725", "000961", "003095", "163406", "005918", "012414"]
    
    async with async_session() as session:
        for code in hot_funds:
            print(f"  获取 {code} 净值...")
            df = fetcher.fetch_fund_nav(code)
            if df.empty:
                continue
            
            count = 0
            for _, row in df.iterrows():
                nav = NavHistory(
                    code=code,
                    date=row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                    nav=float(row['nav']),
                    growth=float(row.get('growth', 0) or 0)
                )
                await session.merge(nav)
                count += 1
            await session.commit()
            print(f"    {code}: {count} 条净值数据")
    
    print("净值数据填充完成")

async def main():
    await init_db()
    await seed_fund_list()
    await seed_sample_nav()
    print("\n数据填充完成！")

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: 运行填充**

```bash
cd ~/fund-analyzer && python3 backend/scripts/seed_data.py
```

**Step 3: 验证**

```bash
curl -s "http://localhost:8000/api/fund/search?keyword=易方达" | python3 -m json.tool | head -20
```

**Step 4: Commit**

```bash
git add backend/scripts/ && git commit -m "feat: 基金数据填充脚本"
```

---

## Batch 2: 组合管理功能

### Task 2.1: 组合 API

**Files:**
- Create: `backend/api/portfolio.py`
- Modify: `backend/main.py`

**Step 1: 创建组合 API**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.portfolio import Portfolio, PortfolioHolding
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/portfolio", tags=["组合"])

class HoldingCreate(BaseModel):
    code: str
    weight: float

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    holdings: List[HoldingCreate]

class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: str
    holdings: List[dict]
    created_at: datetime

@router.post("/create")
async def create_portfolio(data: PortfolioCreate, db: AsyncSession = Depends(get_db)):
    """创建基金组合"""
    portfolio = Portfolio(
        name=data.name,
        description=data.description,
        created_at=datetime.now()
    )
    db.add(portfolio)
    await db.flush()
    
    for h in data.holdings:
        holding = PortfolioHolding(
            portfolio_id=portfolio.id,
            code=h.code,
            weight=h.weight
        )
        db.add(holding)
    
    await db.commit()
    return {"id": portfolio.id, "name": portfolio.name, "message": "组合创建成功"}

@router.get("/list")
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    """获取所有组合"""
    result = await db.execute(select(Portfolio))
    portfolios = result.scalars().all()
    
    data = []
    for p in portfolios:
        holdings_result = await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.portfolio_id == p.id)
        )
        holdings = holdings_result.scalars().all()
        data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "holdings": [{"code": h.code, "weight": float(h.weight)} for h in holdings],
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    
    return {"portfolios": data}

@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个组合详情"""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    
    holdings_result = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
    )
    holdings = holdings_result.scalars().all()
    
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "holdings": [{"code": h.code, "weight": float(h.weight)} for h in holdings],
        "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None
    }

@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """删除组合"""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    
    await db.execute(
        PortfolioHolding.__table__.delete().where(PortfolioHolding.portfolio_id == portfolio_id)
    )
    await db.delete(portfolio)
    await db.commit()
    return {"message": "组合已删除"}
```

**Step 2: 注册路由到 main.py**

**Step 3: Commit**

---

### Task 2.2: 组合分析服务

**Files:**
- Create: `backend/services/portfolio_analyzer.py`

**Step 1: 创建组合分析服务**

```python
import pandas as pd
import numpy as np
from typing import Dict, List
from backend.services.data_fetcher import DataFetcher
from backend.services.risk_analyzer import RiskAnalyzer

fetcher = DataFetcher()
risk_analyzer = RiskAnalyzer()

class PortfolioAnalyzer:
    """基金组合分析"""
    
    def analyze_portfolio(self, holdings: List[Dict]) -> Dict:
        """
        分析基金组合
        holdings: [{"code": "110011", "weight": 0.4}, ...]
        """
        nav_data = {}
        for h in holdings:
            df = fetcher.fetch_fund_nav(h["code"])
            if not df.empty:
                nav_data[h["code"]] = df
        
        if not nav_data:
            return {"error": "无法获取基金数据"}
        
        # 计算加权收益
        combined_returns = None
        for h in holdings:
            code = h["code"]
            weight = h["weight"]
            if code not in nav_data:
                continue
            
            df = nav_data[code]
            returns = df.set_index("date")["nav"].pct_change().dropna()
            weighted_returns = returns * weight
            
            if combined_returns is None:
                combined_returns = weighted_returns
            else:
                combined_returns = combined_returns.add(weighted_returns, fill_value=0)
        
        if combined_returns is None or combined_returns.empty:
            return {"error": "无法计算组合收益"}
        
        # 计算组合指标
        cum_returns = (1 + combined_returns).cumprod()
        total_return = (cum_returns.iloc[-1] - 1) * 100
        
        # 波动率
        volatility = combined_returns.std() * np.sqrt(252) * 100
        
        # 最大回撤
        cummax = cum_returns.cummax()
        drawdown = (cum_returns - cummax) / cummax
        max_drawdown = drawdown.min() * 100
        
        # 夏普比率
        risk_free_rate = 0.02
        sharpe = (total_return / 100 - risk_free_rate) / (volatility / 100) if volatility > 0 else 0
        
        # 各基金贡献
        contributions = []
        for h in holdings:
            code = h["code"]
            weight = h["weight"]
            if code in nav_data:
                df = nav_data[code]
                metrics = risk_analyzer.calculate(df["nav"], df["date"])
                contributions.append({
                    "code": code,
                    "weight": weight,
                    "return": metrics.get("total_return", 0),
                    "contribution": metrics.get("total_return", 0) * weight
                })
        
        return {
            "total_return": round(total_return, 2),
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe": round(sharpe, 2),
            "contributions": contributions,
            "nav_history": [
                {"date": d.strftime("%Y-%m-%d"), "value": round(v, 4)}
                for d, v in cum_returns.items()
            ]
        }
```

**Step 2: 添加组合分析 API 到 portfolio.py**

```python
from backend.services.portfolio_analyzer import PortfolioAnalyzer

portfolio_analyzer = PortfolioAnalyzer()

@router.get("/{portfolio_id}/analysis")
async def analyze_portfolio(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """分析组合收益和风险"""
    result = await db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="组合不存在")
    
    holdings_result = await db.execute(
        select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
    )
    holdings = holdings_result.scalars().all()
    
    holdings_data = [{"code": h.code, "weight": float(h.weight)} for h in holdings]
    analysis = portfolio_analyzer.analyze_portfolio(holdings_data)
    
    return {"portfolio_id": portfolio_id, "name": portfolio.name, "analysis": analysis}
```

**Step 3: Commit**

---

## Batch 3: 前端页面完善

### Task 3.1: 定投回测页面

**Files:**
- Create: `frontend/src/views/Backtest.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: 创建回测页面**

```vue
<template>
  <div class="backtest-page">
    <el-card>
      <template #header>
        <h2>💰 定投回测</h2>
      </template>
      
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="基金代码">
              <el-input v-model="form.code" placeholder="如 110011" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="每次金额">
              <el-input-number v-model="form.amount" :min="100" :step="100" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="定投频率">
              <el-select v-model="form.frequency">
                <el-option label="每月" value="monthly" />
                <el-option label="每周" value="weekly" />
                <el-option label="每两周" value="biweekly" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="投资策略">
              <el-select v-model="form.strategy">
                <el-option label="普通定投" value="regular" />
                <el-option label="均线智能定投" value="smart-ma" />
                <el-option label="回撤加仓" value="drawdown" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开始日期">
              <el-date-picker v-model="form.startDate" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="runBacktest" :loading="loading">开始回测</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <el-card v-if="result" style="margin-top: 20px">
      <template #header>
        <h3>回测结果</h3>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6" v-for="(value, key) in metrics" :key="key">
          <el-statistic :title="key" :value="value" />
        </el-col>
      </el-row>
      
      <div ref="chartRef" style="height: 400px; margin-top: 20px"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const form = reactive({
  code: '',
  amount: 1000,
  frequency: 'monthly',
  strategy: 'regular',
  startDate: '2020-01-01'
})

const loading = ref(false)
const result = ref(null)
const chartRef = ref(null)

const metrics = ref({})

const runBacktest = async () => {
  if (!form.code) return
  loading.value = true
  
  try {
    const response = await axios.post(`/api/backtest/${form.strategy}`, {
      code: form.code,
      amount: form.amount,
      frequency: form.frequency,
      start_date: form.startDate
    })
    
    result.value = response.data
    
    if (response.data.summary) {
      metrics.value = {
        '总投入': response.data.summary.total_invest + '元',
        '最终价值': response.data.summary.final_value + '元',
        '总收益': response.data.summary.total_profit + '元',
        '收益率': response.data.summary.total_return + '%',
        '年化收益': response.data.summary.annual_return + '%',
        '最大回撤': response.data.summary.max_drawdown + '%'
      }
    }
    
    if (response.data.value_history) {
      drawChart(response.data.value_history)
    }
  } catch (error) {
    console.error('回测失败:', error)
  } finally {
    loading.value = false
  }
}

const drawChart = (history) => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    title: { text: '资产走势' },
    tooltip: { trigger: 'axis' },
    xAxis: { data: history.map(h => h.date) },
    yAxis: { type: 'value' },
    series: [
      { name: '资产价值', data: history.map(h => h.value), type: 'line', smooth: true },
      { name: '累计投入', data: history.map(h => h.invest), type: 'line', lineStyle: { type: 'dashed' } }
    ]
  })
}
</script>
```

**Step 2: 添加路由**

**Step 3: Commit**

---

### Task 3.2: 组合管理页面

**Files:**
- Create: `frontend/src/views/Portfolio.vue`

**Step 1: 创建组合页面**

```vue
<template>
  <div class="portfolio-page">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <h2>📊 基金组合</h2>
          <el-button type="primary" @click="showCreate = true">创建组合</el-button>
        </div>
      </template>
      
      <el-table :data="portfolios" style="width: 100%">
        <el-table-column prop="name" label="组合名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="持仓">
          <template #default="{ row }">
            <el-tag v-for="h in row.holdings" :key="h.code" style="margin-right: 5px">
              {{ h.code }} ({{ (h.weight * 100).toFixed(0) }}%)
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="analyzePortfolio(row.id)">分析</el-button>
            <el-button size="small" type="danger" @click="deletePortfolio(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 创建组合对话框 -->
    <el-dialog v-model="showCreate" title="创建组合" width="600px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="持仓">
          <div v-for="(h, i) in createForm.holdings" :key="i" style="display: flex; gap: 10px; margin-bottom: 10px">
            <el-input v-model="h.code" placeholder="基金代码" style="width: 200px" />
            <el-input-number v-model="h.weight" :min="0.01" :max="1" :step="0.1" :precision="2" />
            <el-button @click="createForm.holdings.splice(i, 1)">删除</el-button>
          </div>
          <el-button @click="createForm.holdings.push({ code: '', weight: 0.2 })">添加持仓</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createPortfolio">创建</el-button>
      </template>
    </el-dialog>
    
    <!-- 分析结果对话框 -->
    <el-dialog v-model="showAnalysis" title="组合分析" width="800px">
      <div v-if="analysis">
        <el-row :gutter="20" style="margin-bottom: 20px">
          <el-col :span="6">
            <el-statistic title="总收益" :value="analysis.total_return + '%'" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="波动率" :value="analysis.volatility + '%'" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最大回撤" :value="analysis.max_drawdown + '%'" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="夏普比率" :value="analysis.sharpe" />
          </el-col>
        </el-row>
        
        <h4>各基金贡献</h4>
        <el-table :data="analysis.contributions" style="width: 100%">
          <el-table-column prop="code" label="基金代码" />
          <el-table-column label="权重">
            <template #default="{ row }">{{ (row.weight * 100).toFixed(0) }}%</template>
          </el-table-column>
          <el-table-column label="收益">
            <template #default="{ row }">{{ row.return }}%</template>
          </el-table-column>
          <el-table-column label="贡献">
            <template #default="{ row }">{{ row.contribution.toFixed(2) }}%</template>
          </el-table-column>
        </el-table>
        
        <div ref="analysisChartRef" style="height: 300px; margin-top: 20px"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const portfolios = ref([])
const showCreate = ref(false)
const showAnalysis = ref(false)
const analysis = ref(null)
const analysisChartRef = ref(null)

const createForm = ref({
  name: '',
  description: '',
  holdings: [{ code: '', weight: 0.2 }]
})

const loadPortfolios = async () => {
  const response = await axios.get('/api/portfolio/list')
  portfolios.value = response.data.portfolios || []
}

const createPortfolio = async () => {
  await axios.post('/api/portfolio/create', createForm.value)
  showCreate.value = false
  createForm.value = { name: '', description: '', holdings: [{ code: '', weight: 0.2 }] }
  await loadPortfolios()
}

const deletePortfolio = async (id) => {
  await axios.delete(`/api/portfolio/${id}`)
  await loadPortfolios()
}

const analyzePortfolio = async (id) => {
  const response = await axios.get(`/api/portfolio/${id}/analysis`)
  analysis.value = response.data.analysis
  showAnalysis.value = true
  
  if (analysis.value.nav_history) {
    setTimeout(() => {
      if (!analysisChartRef.value) return
      const chart = echarts.init(analysisChartRef.value)
      chart.setOption({
        title: { text: '组合净值走势' },
        tooltip: { trigger: 'axis' },
        xAxis: { data: analysis.value.nav_history.map(h => h.date) },
        yAxis: { type: 'value' },
        series: [{ data: analysis.value.nav_history.map(h => h.value), type: 'line', smooth: true }]
      })
    }, 100)
  }
}

onMounted(loadPortfolios)
</script>
```

**Step 2: 添加路由**

**Step 3: Commit**

---

### Task 3.3: 更新导航栏

**Files:**
- Modify: `frontend/src/App.vue`

**Step 1: 添加导航菜单**

```vue
<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <h1 @click="goHome">📊 基金分析器</h1>
        <el-menu mode="horizontal" :router="true" background-color="transparent" text-color="#fff" active-text-color="#ffd04b">
          <el-menu-item index="/search">搜索</el-menu-item>
          <el-menu-item index="/backtest">回测</el-menu-item>
          <el-menu-item index="/portfolio">组合</el-menu-item>
          <el-menu-item index="/ranking">排行</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>
```

**Step 2: Commit**

---

## Batch 4: 监控 + 报告（第三阶段）

### Task 4.1: 持仓监控 API

**Files:**
- Create: `backend/api/monitor.py`

**Step 1: 创建监控 API**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.user import UserFund
from backend.services.data_fetcher import DataFetcher
from backend.services.risk_analyzer import RiskAnalyzer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/monitor", tags=["监控"])
fetcher = DataFetcher()
risk_analyzer = RiskAnalyzer()

class AddHolding(BaseModel):
    code: str
    buy_price: float
    buy_date: str
    amount: float

@router.post("/add")
async def add_holding(data: AddHolding, db: AsyncSession = Depends(get_db)):
    """添加持仓"""
    holding = UserFund(
        code=data.code,
        action="hold",
        buy_price=data.buy_price,
        buy_date=datetime.strptime(data.buy_date, "%Y-%m-%d").date(),
        amount=data.amount,
        created_at=datetime.now()
    )
    db.add(holding)
    await db.commit()
    return {"message": "持仓添加成功"}

@router.get("/holdings")
async def get_holdings(db: AsyncSession = Depends(get_db)):
    """获取所有持仓"""
    result = await db.execute(select(UserFund).where(UserFund.action == "hold"))
    holdings = result.scalars().all()
    
    data = []
    for h in holdings:
        df = fetcher.fetch_fund_nav(h.code)
        current_nav = float(df.iloc[-1]["nav"]) if not df.empty else 0
        buy_nav = float(h.buy_price)
        profit = ((current_nav - buy_nav) / buy_nav * 100) if buy_nav > 0 else 0
        
        data.append({
            "id": h.id,
            "code": h.code,
            "buy_price": buy_nav,
            "current_nav": current_nav,
            "profit": round(profit, 2),
            "amount": float(h.amount),
            "buy_date": h.buy_date.isoformat() if h.buy_date else None
        })
    
    return {"holdings": data}

@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    """获取风险提醒"""
    result = await db.execute(select(UserFund).where(UserFund.action == "hold"))
    holdings = result.scalars().all()
    
    alerts = []
    for h in holdings:
        df = fetcher.fetch_fund_nav(h.code)
        if df.empty:
            continue
        
        metrics = risk_analyzer.calculate(df["nav"], df["date"])
        
        # 回撤提醒
        if metrics.get("max_drawdown", 0) < -15:
            alerts.append({
                "code": h.code,
                "type": "回撤警告",
                "message": f"最大回撤 {metrics['max_drawdown']}%，超过 15% 阈值",
                "level": "warning"
            })
        
        # 收益提醒
        current_nav = float(df.iloc[-1]["nav"])
        buy_nav = float(h.buy_price)
        profit = (current_nav - buy_nav) / buy_nav * 100
        
        if profit > 30:
            alerts.append({
                "code": h.code,
                "type": "止盈提醒",
                "message": f"收益已达 {profit:.1f}%，建议考虑止盈",
                "level": "success"
            })
    
    return {"alerts": alerts}
```

**Step 2: 注册路由**

**Step 3: Commit**

---

### Task 4.2: 基金经理分析 API

**Files:**
- Modify: `backend/api/fund.py`

**Step 1: 添加基金经理分析**

```python
@router.get("/manager/{manager_name}")
async def fund_manager_analysis(manager_name: str):
    """基金经理分析"""
    # 从基金列表中筛选该经理管理的基金
    df = fetcher.fetch_fund_list("全部")
    if df.empty:
        return {"error": "无法获取基金数据"}
    
    manager_funds = df[df["基金经理"].str.contains(manager_name, na=False)]
    
    if manager_funds.empty:
        return {"error": f"未找到基金经理 {manager_name}"}
    
    funds_data = []
    for _, row in manager_funds.iterrows():
        code = str(row.get("基金代码", ""))
        nav_df = fetcher.fetch_fund_nav(code)
        if not nav_df.empty:
            metrics = risk_analyzer.calculate(nav_df["nav"], nav_df["date"])
            funds_data.append({
                "code": code,
                "name": str(row.get("基金简称", "")),
                "type": str(row.get("基金类型", "")),
                "scale": float(row.get("基金规模(亿元)", 0) or 0),
                "metrics": metrics
            })
    
    return {
        "manager": manager_name,
        "fund_count": len(funds_data),
        "funds": funds_data
    }
```

**Step 2: Commit**

---

### Task 4.3: AI 基金诊断报告

**Files:**
- Create: `backend/services/report_generator.py`
- Create: `backend/api/report.py`

**Step 1: 创建报告生成服务**

```python
from backend.services.data_fetcher import DataFetcher
from backend.services.risk_analyzer import RiskAnalyzer
from typing import Dict

fetcher = DataFetcher()
risk_analyzer = RiskAnalyzer()

class ReportGenerator:
    """基金诊断报告生成"""
    
    def generate_fund_report(self, code: str) -> Dict:
        """生成基金诊断报告"""
        df = fetcher.fetch_fund_nav(code)
        if df.empty:
            return {"error": "无法获取基金数据"}
        
        info = fetcher.fetch_fund_info(code)
        metrics = risk_analyzer.calculate(df["nav"], df["date"])
        
        # 生成文字分析
        analysis = self._analyze_metrics(metrics, info)
        
        return {
            "code": code,
            "info": info,
            "metrics": metrics,
            "analysis": analysis,
            "nav_history": [
                {"date": row["date"].strftime("%Y-%m-%d"), "nav": float(row["nav"])}
                for _, row in df.iterrows()
            ]
        }
    
    def _analyze_metrics(self, metrics: Dict, info: Dict) -> str:
        """根据指标生成分析文字"""
        lines = []
        
        # 收益分析
        annual_return = metrics.get("annual_return", 0)
        if annual_return > 15:
            lines.append(f"✅ 年化收益率 {annual_return}%，表现优秀")
        elif annual_return > 8:
            lines.append(f"📊 年化收益率 {annual_return}%，表现良好")
        else:
            lines.append(f"⚠️ 年化收益率 {annual_return}%，表现一般")
        
        # 风险分析
        max_drawdown = metrics.get("max_drawdown", 0)
        if max_drawdown < -30:
            lines.append(f"🔴 最大回撤 {max_drawdown}%，风险较高")
        elif max_drawdown < -15:
            lines.append(f"🟡 最大回撤 {max_drawdown}%，风险中等")
        else:
            lines.append(f"🟢 最大回撤 {max_drawdown}%，风险较低")
        
        # 夏普比率
        sharpe = metrics.get("sharpe", 0)
        if sharpe > 1:
            lines.append(f"✅ 夏普比率 {sharpe}，风险调整收益较好")
        elif sharpe > 0.5:
            lines.append(f"📊 夏普比率 {sharpe}，风险调整收益一般")
        else:
            lines.append(f"⚠️ 夏普比率 {sharpe}，风险调整收益较差")
        
        # 综合建议
        if annual_return > 10 and max_drawdown > -20 and sharpe > 0.8:
            lines.append("💡 综合评估：该基金收益风险比较均衡，适合长期持有")
        elif annual_return > 15 and max_drawdown < -25:
            lines.append("💡 综合评估：该基金收益较高但波动大，适合风险承受能力较强的投资者")
        else:
            lines.append("💡 综合评估：建议结合其他基金进行组合配置")
        
        return "\n".join(lines)
```

**Step 2: 创建报告 API**

```python
from fastapi import APIRouter
from backend.services.report_generator import ReportGenerator

router = APIRouter(prefix="/api/report", tags=["报告"])
report_gen = ReportGenerator()

@router.get("/fund/{code}")
async def fund_report(code: str):
    """生成基金诊断报告"""
    report = report_gen.generate_fund_report(code)
    return report
```

**Step 3: Commit**

---

### Task 4.4: Vue3 监控页面

**Files:**
- Create: `frontend/src/views/Monitor.vue`

**Step 1: 创建监控页面**

```vue
<template>
  <div class="monitor-page">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <h2>📈 持仓监控</h2>
              <el-button type="primary" size="small" @click="showAdd = true">添加持仓</el-button>
            </div>
          </template>
          
          <el-table :data="holdings" style="width: 100%">
            <el-table-column prop="code" label="基金代码" width="100" />
            <el-table-column label="买入价" width="100">
              <template #default="{ row }">{{ row.buy_price }}</template>
            </el-table-column>
            <el-table-column label="当前净值" width="100">
              <template #default="{ row }">{{ row.current_nav }}</template>
            </el-table-column>
            <el-table-column label="收益" width="100">
              <template #default="{ row }">
                <span :class="row.profit >= 0 ? 'positive' : 'negative'">{{ row.profit }}%</span>
              </template>
            </el-table-column>
            <el-table-column label="金额" width="120">
              <template #default="{ row }">{{ row.amount }}元</template>
            </el-table-column>
            <el-table-column prop="buy_date" label="买入日期" />
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <h2>🔔 风险提醒</h2>
          </template>
          
          <div v-if="alerts.length === 0" style="text-align: center; color: #999; padding: 20px">
            暂无提醒
          </div>
          
          <div v-for="alert in alerts" :key="alert.code + alert.type" 
               :class="['alert-item', alert.level]"
               style="padding: 10px; margin-bottom: 10px; border-radius: 4px">
            <div style="font-weight: bold">{{ alert.type }}</div>
            <div style="font-size: 12px; color: #666">{{ alert.code }}</div>
            <div style="margin-top: 5px">{{ alert.message }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 添加持仓对话框 -->
    <el-dialog v-model="showAdd" title="添加持仓" width="400px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="基金代码">
          <el-input v-model="addForm.code" />
        </el-form-item>
        <el-form-item label="买入价">
          <el-input-number v-model="addForm.buy_price" :min="0" :step="0.01" :precision="4" />
        </el-form-item>
        <el-form-item label="买入日期">
          <el-date-picker v-model="addForm.buy_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="addForm.amount" :min="100" :step="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="addHolding">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const holdings = ref([])
const alerts = ref([])
const showAdd = ref(false)

const addForm = ref({
  code: '',
  buy_price: 0,
  buy_date: '',
  amount: 1000
})

const loadData = async () => {
  const [holdingsRes, alertsRes] = await Promise.all([
    axios.get('/api/monitor/holdings'),
    axios.get('/api/monitor/alerts')
  ])
  holdings.value = holdingsRes.data.holdings || []
  alerts.value = alertsRes.data.alerts || []
}

const addHolding = async () => {
  await axios.post('/api/monitor/add', addForm.value)
  showAdd.value = false
  addForm.value = { code: '', buy_price: 0, buy_date: '', amount: 1000 }
  await loadData()
}

onMounted(loadData)
</script>

<style scoped>
.positive { color: #ef4444; }
.negative { color: #10b981; }
.alert-item.warning { background: #fef3cd; border: 1px solid #ffc107; }
.alert-item.success { background: #d1fae5; border: 1px solid #10b981; }
.alert-item.danger { background: #fee2e2; border: 1px solid #ef4444; }
</style>
```

**Step 2: Commit**

---

## Batch 5: 最终集成

### Task 5.1: 注册所有路由 + 构建前端

**Step 1: 更新 main.py 注册所有路由**

**Step 2: 重新构建前端**

```bash
cd ~/fund-analyzer/frontend && npm run build
cp -r dist/* /var/www/fund/
```

**Step 3: 重启后端**

**Step 4: 测试所有 API**

**Step 5: Final Commit + Push**

---

## 执行顺序

```
Batch 1: 数据填充（Task 1.1）← 最紧急
Batch 2: 组合管理（Task 2.1 + 2.2）← 可并行
Batch 3: 前端页面（Task 3.1 + 3.2 + 3.3）← 可并行
Batch 4: 监控报告（Task 4.1 + 4.2 + 4.3 + 4.4）← 可并行
Batch 5: 集成测试 + 部署
```
