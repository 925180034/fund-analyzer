# 基金分析平台 V2 — 第一阶段实施计划

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** 搭建 FastAPI + Vue3 + PostgreSQL + Redis 基金分析平台，实现数据采集、缓存、搜索、详情、排行、4433筛选、GoFundBot集成。

**Architecture:** FastAPI 单体应用，按 api/services/models 分层。PostgreSQL 存储基金数据，Redis 做缓存。前端 Vue3 + Element Plus + ECharts。

**Tech Stack:** FastAPI, SQLAlchemy, asyncpg, Redis, APScheduler, AKShare, Vue3, Vite, Element Plus, ECharts, PyPortfolioOpt

---

## Task 1: 项目脚手架 — 后端

**Files:**
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/redis_client.py`
- Create: `requirements.txt`
- Create: `.env.example`

**Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
redis==5.0.0
apscheduler==3.10.0
akshare>=1.14.0
pandas>=2.0.0
numpy>=1.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx==0.27.0
python-dotenv==1.0.0
```

**Step 2: 创建 .env.example**

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fund_analyzer
REDIS_URL=redis://localhost:6379/0
GOFUNDBOT_API_URL=http://localhost:8001
AKSHARE_PROXY=
```

**Step 3: 创建 backend/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/fund_analyzer"
    redis_url: str = "redis://localhost:6379/0"
    gofundbot_api_url: str = "http://localhost:8001"
    akshare_proxy: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

**Step 4: 创建 backend/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**Step 5: 创建 backend/redis_client.py**

```python
import redis.asyncio as redis
from backend.config import get_settings

settings = get_settings()
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def get_redis():
    return redis_client
```

**Step 6: 创建 backend/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="基金分析平台", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 7: 安装依赖并验证**

```bash
cd ~/fund-analyzer
pip install -r requirements.txt
cd backend && python -c "from main import app; print('OK')"
```

**Step 8: Commit**

```bash
git add requirements.txt .env.example backend/
git commit -m "feat: 后端脚手架 — FastAPI + SQLAlchemy + Redis"
```

---

## Task 2: PostgreSQL 安装 + 数据库创建

**Files:**
- Create: `scripts/init_db.sh`

**Step 1: 安装 PostgreSQL**

```bash
apt-get update && apt-get install -y postgresql postgresql-client
systemctl start postgresql
```

**Step 2: 创建数据库和用户**

```bash
sudo -u postgres psql -c "CREATE USER fund WITH PASSWORD 'fund123';"
sudo -u postgres psql -c "CREATE DATABASE fund_analyzer OWNER fund;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fund_analyzer TO fund;"
```

**Step 3: 创建 .env**

```bash
cp .env.example .env
# 修改 DATABASE_URL 密码为 fund123
```

**Step 4: 验证连接**

```bash
python -c "
import asyncio
from backend.database import engine
async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('DB OK:', result.scalar())
asyncio.run(test())
"
```

**Step 5: Commit**

```bash
git add scripts/ .env
git commit -m "feat: PostgreSQL 数据库初始化"
```

---

## Task 3: 数据模型 — 基金表

**Files:**
- Create: `backend/models/__init__.py`
- Create: `backend/models/fund.py`
- Create: `tests/test_fund_model.py`

**Step 1: 创建 tests/test_fund_model.py**

```python
import pytest
from backend.models.fund import Fund

def test_fund_create():
    fund = Fund(code="110011", name="易方达中小盘混合", type="混合型")
    assert fund.code == "110011"
    assert fund.name == "易方达中小盘混合"

def test_fund_repr():
    fund = Fund(code="110011", name="测试基金")
    assert "110011" in repr(fund)
```

**Step 2: 运行测试 — 确认失败**

```bash
pytest tests/test_fund_model.py -v
# Expected: FAIL — ModuleNotFoundError
```

**Step 3: 创建 backend/models/fund.py**

```python
from sqlalchemy import Column, String, Date, Numeric, DateTime
from backend.database import Base

class Fund(Base):
    __tablename__ = "funds"
    
    code = Column(String(10), primary_key=True)
    name = Column(String(100))
    type = Column(String(20))
    company = Column(String(50))
    manager = Column(String(50))
    establish_date = Column(Date)
    scale = Column(Numeric(12, 2))
    fee_buy = Column(Numeric(5, 4))
    fee_sell = Column(Numeric(5, 4))
    fee_manage = Column(Numeric(5, 4))
    updated_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Fund {self.code} {self.name}>"
```

**Step 4: 运行测试 — 确认通过**

```bash
pytest tests/test_fund_model.py -v
# Expected: 2 passed
```

**Step 5: Commit**

```bash
git add backend/models/ tests/
git commit -m "feat: Fund 数据模型"
```

---

## Task 4: 数据模型 — 净值表

**Files:**
- Create: `backend/models/nav.py`
- Create: `tests/test_nav_model.py`

**Step 1: 创建 tests/test_nav_model.py**

```python
from backend.models.nav import NavHistory
from datetime import date

def test_nav_create():
    nav = NavHistory(code="110011", date=date(2024,1,1), nav=3.5678)
    assert nav.code == "110011"
    assert float(nav.nav) == 3.5678
```

**Step 2: 运行测试 — 确认失败**

**Step 3: 创建 backend/models/nav.py**

```python
from sqlalchemy import Column, String, Date, Numeric
from backend.database import Base

class NavHistory(Base):
    __tablename__ = "nav_history"
    
    code = Column(String(10), primary_key=True)
    date = Column(Date, primary_key=True)
    nav = Column(Numeric(10, 4))
    acc_nav = Column(Numeric(10, 4))
    growth = Column(Numeric(8, 4))
```

**Step 4: 运行测试 — 确认通过**

**Step 5: Commit**

```bash
git add backend/models/nav.py tests/
git commit -m "feat: NavHistory 数据模型"
```

---

## Task 5: 数据模型 — 排行 + 收藏 + 组合

**Files:**
- Create: `backend/models/ranking.py`
- Create: `backend/models/portfolio.py`
- Create: `backend/models/user.py`

**Step 1: 创建 backend/models/ranking.py**

```python
from sqlalchemy import Column, String, Date, Integer
from backend.database import Base

class FundRanking(Base):
    __tablename__ = "fund_rankings"
    
    code = Column(String(10), primary_key=True)
    rank_date = Column(Date, primary_key=True)
    type = Column(String(20))
    rank_3m = Column(Integer)
    rank_6m = Column(Integer)
    rank_1y = Column(Integer)
    rank_3y = Column(Integer)
    total_count = Column(Integer)
```

**Step 2: 创建 backend/models/portfolio.py**

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    description = Column(Text)
    created_at = Column(DateTime)
    
    holdings = relationship("PortfolioHolding", back_populates="portfolio")

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), primary_key=True)
    code = Column(String(10), primary_key=True)
    weight = Column(Numeric(5, 4))
    
    portfolio = relationship("Portfolio", back_populates="holdings")
```

**Step 3: 创建 backend/models/user.py**

```python
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime
from backend.database import Base

class UserFund(Base):
    __tablename__ = "user_funds"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10))
    action = Column(String(20))  # watch/hold/sold
    buy_price = Column(Numeric(10, 4))
    buy_date = Column(Date)
    amount = Column(Numeric(12, 2))
    created_at = Column(DateTime)
```

**Step 4: 更新 backend/models/__init__.py**

```python
from backend.models.fund import Fund
from backend.models.nav import NavHistory
from backend.models.ranking import FundRanking
from backend.models.portfolio import Portfolio, PortfolioHolding
from backend.models.user import UserFund

__all__ = ["Fund", "NavHistory", "FundRanking", "Portfolio", "PortfolioHolding", "UserFund"]
```

**Step 5: Commit**

```bash
git add backend/models/
git commit -m "feat: 排行/组合/用户数据模型"
```

---

## Task 6: AKShare 数据采集服务

**Files:**
- Create: `backend/services/data_fetcher.py`
- Create: `tests/test_data_fetcher.py`

**Step 1: 创建 tests/test_data_fetcher.py**

```python
import pytest
from backend.services.data_fetcher import DataFetcher

def test_fetcher_init():
    fetcher = DataFetcher()
    assert fetcher is not None
```

**Step 2: 运行测试 — 确认失败**

**Step 3: 创建 backend/services/data_fetcher.py**

```python
import akshare as ak
import pandas as pd
from datetime import datetime

class DataFetcher:
    """AKShare 数据采集服务"""
    
    def fetch_fund_list(self, fund_type="全部"):
        """获取基金列表"""
        try:
            df = ak.fund_open_fund_rank_em(symbol=fund_type)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            print(f"获取基金列表失败: {e}")
            return pd.DataFrame()
    
    def fetch_fund_nav(self, code):
        """获取基金净值历史"""
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is not None and not df.empty:
                df.columns = ['date', 'nav', 'growth']
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                return df
        except Exception as e:
            print(f"获取基金 {code} 净值失败: {e}")
        return pd.DataFrame()
    
    def fetch_fund_info(self, code):
        """获取基金基本信息"""
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="基金概况")
            if df is not None and not df.empty:
                info = {}
                for _, row in df.iterrows():
                    info[row.iloc[0]] = str(row.iloc[1])
                return info
        except Exception as e:
            print(f"获取基金 {code} 信息失败: {e}")
        return {}
```

**Step 4: 运行测试 — 确认通过**

**Step 5: Commit**

```bash
git add backend/services/data_fetcher.py tests/
git commit -m "feat: AKShare 数据采集服务"
```

---

## Task 7: Redis 缓存管理服务

**Files:**
- Create: `backend/services/cache_manager.py`
- Create: `tests/test_cache_manager.py`

**Step 1: 创建 tests/test_cache_manager.py**

```python
import pytest
from backend.services.cache_manager import CacheManager

def test_cache_manager_init():
    cm = CacheManager()
    assert cm is not None
```

**Step 2: 创建 backend/services/cache_manager.py**

```python
import json
from backend.redis_client import redis_client

class CacheManager:
    """Redis 缓存管理"""
    
    DEFAULT_TTL = 3600  # 1小时
    FUND_LIST_TTL = 86400  # 24小时
    NAV_TTL = 3600  # 1小时
    
    async def get(self, key):
        """获取缓存"""
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    
    async def set(self, key, value, ttl=None):
        """设置缓存"""
        ttl = ttl or self.DEFAULT_TTL
        await redis_client.set(key, json.dumps(value, default=str), ex=ttl)
    
    async def delete(self, key):
        """删除缓存"""
        await redis_client.delete(key)
    
    async def get_fund_list(self, fund_type="全部"):
        """获取基金列表缓存"""
        return await self.get(f"fund_list:{fund_type}")
    
    async def set_fund_list(self, fund_type, data):
        """设置基金列表缓存"""
        await self.set(f"fund_list:{fund_type}", data, self.FUND_LIST_TTL)
    
    async def get_fund_nav(self, code):
        """获取基金净值缓存"""
        return await self.get(f"fund_nav:{code}")
    
    async def set_fund_nav(self, code, data):
        """设置基金净值缓存"""
        await self.set(f"fund_nav:{code}", data, self.NAV_TTL)
```

**Step 3: 运行测试 — 确认通过**

**Step 4: Commit**

```bash
git add backend/services/cache_manager.py tests/
git commit -m "feat: Redis 缓存管理服务"
```

---

## Task 8: 基金搜索 API

**Files:**
- Create: `backend/api/__init__.py`
- Create: `backend/api/fund.py`
- Create: `tests/test_fund_api.py`

**Step 1: 创建 tests/test_fund_api.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_search_fund():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/fund/search?keyword=易方达")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
```

**Step 2: 运行测试 — 确认失败**

**Step 3: 创建 backend/api/fund.py**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.data_fetcher import DataFetcher
from backend.services.cache_manager import CacheManager

router = APIRouter(prefix="/api/fund", tags=["基金"])
fetcher = DataFetcher()
cache = CacheManager()

@router.get("/search")
async def search_fund(keyword: str = Query(..., description="搜索关键词")):
    """搜索基金"""
    # 先查缓存
    cached = await cache.get_fund_list("全部")
    if not cached:
        df = fetcher.fetch_fund_list("全部")
        if df.empty:
            return {"results": []}
        cached = df.to_dict(orient="records")
        await cache.set_fund_list("全部", cached)
    
    # 搜索
    results = []
    for item in cached:
        name = str(item.get("基金简称", ""))
        code = str(item.get("基金代码", ""))
        if keyword in name or keyword in code:
            results.append({
                "code": code,
                "name": name,
                "type": str(item.get("基金类型", "")),
                "nav": float(item.get("单位净值", 0) or 0),
                "day_growth": float(item.get("日增长率", 0) or 0)
            })
    
    return {"results": results[:20]}
```

**Step 4: 注册路由到 main.py**

```python
from backend.api.fund import router as fund_router
app.include_router(fund_router)
```

**Step 5: 运行测试 — 确认通过**

**Step 6: Commit**

```bash
git add backend/api/ tests/ backend/main.py
git commit -m "feat: 基金搜索 API"
```

---

## Task 9: 基金详情 API（含风险指标）

**Files:**
- Create: `backend/services/risk_analyzer.py`
- Modify: `backend/api/fund.py`
- Create: `tests/test_risk_analyzer.py`

**Step 1: 创建 tests/test_risk_analyzer.py**

```python
import pytest
import pandas as pd
from backend.services.risk_analyzer import RiskAnalyzer

def test_calculate_metrics():
    analyzer = RiskAnalyzer()
    navs = pd.Series([1.0, 1.1, 1.05, 1.15, 1.2])
    dates = pd.Series(pd.date_range("2023-01-01", periods=5))
    metrics = analyzer.calculate(navs, dates)
    assert "annual_return" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe" in metrics
    assert "volatility" in metrics
```

**Step 2: 创建 backend/services/risk_analyzer.py**

```python
import pandas as pd
import numpy as np

class RiskAnalyzer:
    """风险指标计算"""
    
    RISK_FREE_RATE = 0.02
    
    def calculate(self, nav_series, dates=None):
        """计算风险指标"""
        if len(nav_series) < 2:
            return {}
        
        returns = nav_series.pct_change().dropna()
        
        total_days = (dates.iloc[-1] - dates.iloc[0]).days if dates is not None and len(dates) >= 2 else len(nav_series)
        
        total_return = (nav_series.iloc[-1] / nav_series.iloc[0]) - 1
        annual_return = (1 + total_return) ** (365 / total_days) - 1 if total_days > 0 else 0
        
        volatility = returns.std() * np.sqrt(252)
        sharpe = (annual_return - self.RISK_FREE_RATE) / volatility if volatility > 0 else 0
        
        cummax = nav_series.cummax()
        drawdown = (nav_series - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # Calmar Ratio
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino = (annual_return - self.RISK_FREE_RATE) / downside_std if downside_std > 0 else 0
        
        # 月度胜率
        if dates is not None:
            monthly = nav_series.groupby(dates.dt.to_period("M")).last().pct_change().dropna()
            win_rate = (monthly > 0).sum() / len(monthly) if len(monthly) > 0 else 0
        else:
            win_rate = 0
        
        return {
            "total_return": round(total_return * 100, 2),
            "annual_return": round(annual_return * 100, 2),
            "volatility": round(volatility * 100, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "calmar": round(calmar, 2),
            "sortino": round(sortino, 2),
            "win_rate": round(win_rate * 100, 2),
            "total_days": total_days
        }
```

**Step 3: 添加基金详情路由到 backend/api/fund.py**

```python
from backend.services.risk_analyzer import RiskAnalyzer

risk_analyzer = RiskAnalyzer()

@router.get("/detail/{code}")
async def fund_detail(code: str):
    """基金详情"""
    nav_df = fetcher.fetch_fund_nav(code)
    if nav_df.empty:
        return {"error": "未找到基金数据"}
    
    metrics = risk_analyzer.calculate(nav_df['nav'], nav_df['date'])
    info = fetcher.fetch_fund_info(code)
    
    nav_history = []
    for _, row in nav_df.iterrows():
        nav_history.append({
            "date": row['date'].strftime('%Y-%m-%d'),
            "nav": round(float(row['nav']), 4),
            "growth": round(float(row.get('growth', 0)), 2)
        })
    
    return {
        "code": code,
        "info": info,
        "metrics": metrics,
        "nav_history": nav_history
    }
```

**Step 4: 运行测试 — 确认通过**

**Step 5: Commit**

```bash
git add backend/services/risk_analyzer.py backend/api/fund.py tests/
git commit -m "feat: 基金详情 API + 风险指标（Calmar/Sortino/胜率）"
```

---

## Task 10: 4433 真排名筛选

**Files:**
- Create: `backend/services/fund_screener.py`
- Create: `backend/api/screen.py`
- Create: `tests/test_fund_screener.py`

**Step 1: 创建 tests/test_fund_screener.py**

```python
import pytest
import pandas as pd
from backend.services.fund_screener import FundScreener

def test_4433_score():
    screener = FundScreener()
    # 模拟同类型排名数据
    rankings = {
        "110011": {"rank_1y": 10, "total": 100, "rank_3y": 20, "total_3y": 80, "rank_6m": 15, "total_6m": 100, "rank_3m": 30, "total_3m": 100}
    }
    score = screener.calculate_4433_score(rankings["110011"])
    assert score["total"] > 0
    assert "details" in score
```

**Step 2: 创建 backend/services/fund_screener.py**

```python
class FundScreener:
    """4433 法则筛选器"""
    
    def calculate_4433_score(self, ranking):
        """
        真正的 4433 评分
        - 近1年排名前 25% → 25分
        - 近3年排名前 25% → 25分
        - 近6月排名前 33% → 25分
        - 近3月排名前 33% → 25分
        """
        score = 0
        details = []
        
        checks = [
            ("近1年", "rank_1y", "total", 0.25, 25),
            ("近3年", "rank_3y", "total_3y", 0.25, 25),
            ("近6月", "rank_6m", "total_6m", 0.33, 25),
            ("近3月", "rank_3m", "total_3m", 0.33, 25),
        ]
        
        for label, rank_key, total_key, threshold, max_score in checks:
            rank = ranking.get(rank_key)
            total = ranking.get(total_key, ranking.get("total", 0))
            
            if rank is None or total == 0:
                details.append({"period": label, "status": "no_data", "score": 0})
                continue
            
            percentile = rank / total
            passed = percentile <= threshold
            
            details.append({
                "period": label,
                "rank": rank,
                "total": total,
                "percentile": round(percentile * 100, 1),
                "threshold": round(threshold * 100),
                "passed": passed,
                "score": max_score if passed else 0
            })
            
            if passed:
                score += max_score
        
        return {"total": score, "details": details}
```

**Step 3: 创建 backend/api/screen.py**

```python
from fastapi import APIRouter, Query
from backend.services.fund_screener import FundScreener

router = APIRouter(prefix="/api/screen", tags=["筛选"])
screener = FundScreener()

@router.get("/4433")
async def screen_4433(fund_type: str = Query("全部"), min_score: int = Query(50)):
    """4433 法则筛选"""
    # TODO: 从数据库获取排名数据并筛选
    return {"message": "待实现 — 需要先完成数据入库"}
```

**Step 4: 注册路由**

**Step 5: Commit**

```bash
git add backend/services/fund_screener.py backend/api/screen.py tests/
git commit -m "feat: 4433 真排名筛选算法"
```

---

## Task 11: 定时任务 — 每日数据更新

**Files:**
- Create: `backend/tasks/daily_update.py`

**Step 1: 创建 backend/tasks/daily_update.py**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.services.data_fetcher import DataFetcher
from backend.database import async_session
from backend.models.fund import Fund
from datetime import datetime

scheduler = AsyncIOScheduler()
fetcher = DataFetcher()

async def update_fund_list():
    """每日更新基金列表"""
    print(f"[{datetime.now()}] 开始更新基金列表...")
    df = fetcher.fetch_fund_list("全部")
    if df.empty:
        print("获取基金列表失败")
        return
    
    async with async_session() as session:
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
        await session.commit()
    
    print(f"更新完成，共 {len(df)} 只基金")

def start_scheduler():
    """启动定时任务"""
    scheduler.add_job(update_fund_list, 'cron', hour=20, minute=0)  # 每天20:00
    scheduler.start()
    print("定时任务已启动：每日20:00更新基金数据")
```

**Step 2: 在 main.py 中启动定时任务**

```python
from backend.tasks.daily_update import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
```

**Step 3: Commit**

```bash
git add backend/tasks/ backend/main.py
git commit -m "feat: 每日定时数据更新任务"
```

---

## Task 12: GoFundBot API 集成

**Files:**
- Create: `backend/external/gofundbot.py`
- Create: `backend/api/fund.py` (添加估值路由)

**Step 1: 创建 backend/external/gofundbot.py**

```python
import httpx
from backend.config import get_settings

class GoFundBotClient:
    """GoFundBot API 客户端"""
    
    def __init__(self):
        self.base_url = get_settings().gofundbot_api_url
    
    async def get_estimate(self, code: str):
        """获取基金实时估值"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/estimate/{code}", timeout=10)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"GoFundBot 估值请求失败: {e}")
        return None
    
    async def get_market_analysis(self):
        """获取市场分析"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/market/analysis", timeout=10)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"GoFundBot 市场分析请求失败: {e}")
        return None
```

**Step 2: 添加估值路由**

```python
from backend.external.gofundbot import GoFundBotClient

gofundbot = GoFundBotClient()

@router.get("/estimate/{code}")
async def fund_estimate(code: str):
    """基金实时估值（GoFundBot）"""
    result = await gofundbot.get_estimate(code)
    if result:
        return result
    return {"error": "估值服务暂不可用"}
```

**Step 3: Commit**

```bash
git add backend/external/ backend/api/fund.py
git commit -m "feat: GoFundBot API 集成"
```

---

## Task 13: Vue3 前端脚手架

**Files:**
- Create: `frontend/` 目录结构

**Step 1: 创建 Vue3 项目**

```bash
cd ~/fund-analyzer
npm create vite@latest frontend -- --template vue
cd frontend
npm install
npm install vue-router@4 element-plus echarts axios
```

**Step 2: 配置 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

**Step 3: Commit**

```bash
git add frontend/
git commit -m "feat: Vue3 前端脚手架"
```

---

## Task 14: Vue3 基金搜索页面

**Files:**
- Create: `frontend/src/views/FundSearch.vue`
- Create: `frontend/src/api/fund.js`

**Step 1: 创建 frontend/src/api/fund.js**

```javascript
import axios from 'axios'

export async function searchFund(keyword) {
  const response = await axios.get(`/api/fund/search?keyword=${encodeURIComponent(keyword)}`)
  return response.data
}

export async function getFundDetail(code) {
  const response = await axios.get(`/api/fund/detail/${code}`)
  return response.data
}
```

**Step 2: 创建 frontend/src/views/FundSearch.vue**

```vue
<template>
  <div class="fund-search">
    <el-input v-model="keyword" placeholder="输入基金代码或名称" @keyup.enter="search">
      <template #append>
        <el-button @click="search">搜索</el-button>
      </template>
    </el-input>
    
    <el-table :data="results" style="margin-top: 20px" @row-click="goDetail">
      <el-table-column prop="code" label="代码" width="100" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="nav" label="净值" width="100" />
      <el-table-column prop="day_growth" label="日涨幅" width="100">
        <template #default="{ row }">
          <span :class="row.day_growth >= 0 ? 'positive' : 'negative'">
            {{ row.day_growth }}%
          </span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchFund } from '../api/fund'

const keyword = ref('')
const results = ref([])
const router = useRouter()

const search = async () => {
  if (!keyword.value) return
  const data = await searchFund(keyword.value)
  results.value = data.results || []
}

const goDetail = (row) => {
  router.push(`/fund/${row.code}`)
}
</script>

<style scoped>
.positive { color: #ef4444; }
.negative { color: #10b981; }
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: Vue3 基金搜索页面"
```

---

## Task 15: Vue3 基金详情页面（含 ECharts）

**Files:**
- Create: `frontend/src/views/FundDetail.vue`

**Step 1: 创建 FundDetail.vue**

```vue
<template>
  <div class="fund-detail" v-if="fund">
    <h2>{{ fund.info['基金简称'] || fund.code }}</h2>
    
    <el-row :gutter="20" style="margin: 20px 0">
      <el-col :span="4" v-for="(value, key) in metricCards" :key="key">
        <el-card shadow="hover">
          <div class="metric-value">{{ value }}</div>
          <div class="metric-label">{{ key }}</div>
        </el-card>
      </el-col>
    </el-row>
    
    <div ref="chartRef" style="height: 400px; margin-top: 20px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getFundDetail } from '../api/fund'
import * as echarts from 'echarts'

const route = useRoute()
const fund = ref(null)
const chartRef = ref(null)

const metricCards = computed(() => {
  if (!fund.value?.metrics) return {}
  const m = fund.value.metrics
  return {
    '总收益': m.total_return + '%',
    '年化收益': m.annual_return + '%',
    '最大回撤': m.max_drawdown + '%',
    '夏普比率': m.sharpe,
    'Calmar': m.calmar,
    'Sortino': m.sortino,
    '月度胜率': m.win_rate + '%',
    '波动率': m.volatility + '%'
  }
})

onMounted(async () => {
  const data = await getFundDetail(route.params.code)
  fund.value = data
  
  // 绘制净值走势图
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    title: { text: '净值走势' },
    tooltip: { trigger: 'axis' },
    xAxis: { data: data.nav_history.map(i => i.date) },
    yAxis: { type: 'value' },
    series: [{
      data: data.nav_history.map(i => i.nav),
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.3 }
    }]
  })
})
</script>
```

**Step 2: Commit**

```bash
git add frontend/src/views/
git commit -m "feat: Vue3 基金详情页面 + ECharts 净值图"
```

---

## 总结

第一阶段共 15 个任务：
- Task 1-5: 脚手架 + 数据模型
- Task 6-7: 数据采集 + 缓存服务
- Task 8-10: 核心 API（搜索/详情/筛选）
- Task 11-12: 定时任务 + 外部集成
- Task 13-15: Vue3 前端页面

预计执行时间：3-5天（subagent 并行可加速）
