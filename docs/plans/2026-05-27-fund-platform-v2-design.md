# 基金分析平台 V2 设计文档

> **日期:** 2026-05-27
> **状态:** 已审批
> **技术栈:** FastAPI + Vue3 + PostgreSQL + Redis + ECharts

---

## 1. 项目定位

综合基金平台，面向个人投资者，核心功能：
- 基金筛选（4433 同类百分位排名）
- 定投回测（普通/均线/回撤加仓）
- 基金组合创建与分析
- 持仓监控与提醒
- AI 基金诊断报告

---

## 2. 技术架构

```
架构类型: 单体应用（模块化组织）

后端: FastAPI + SQLAlchemy + APScheduler
前端: Vue3 + Vite + ECharts + Element Plus
数据库: PostgreSQL（主存储）+ Redis（缓存+任务队列）
数据源: AKShare + GoFundBot API
部署: 直接部署 + Nginx 反向代理
```

---

## 3. 目录结构

```
fund-analyzer/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py          # PostgreSQL 连接
│   ├── redis_client.py      # Redis 连接
│   ├── api/
│   │   ├── fund.py          # 基金搜索/详情/排行
│   │   ├── screen.py        # 筛选（4433等）
│   │   ├── backtest.py      # 定投回测
│   │   ├── portfolio.py     # 组合管理
│   │   └── report.py        # 分析报告
│   ├── services/
│   │   ├── data_fetcher.py  # AKShare 数据获取
│   │   ├── cache_manager.py # 缓存管理
│   │   ├── fund_screener.py # 筛选算法
│   │   ├── backtester.py    # 回测引擎
│   │   ├── risk_analyzer.py # 风险分析
│   │   ├── portfolio.py     # 组合优化
│   │   └── report_gen.py    # 报告生成
│   ├── models/
│   │   ├── fund.py          # 基金模型
│   │   ├── nav.py           # 净值模型
│   │   ├── portfolio.py     # 组合模型
│   │   └── user.py          # 用户模型
│   ├── tasks/
│   │   └── daily_update.py  # 每日数据更新
│   └── external/
│       └── gofundbot.py     # GoFundBot API 集成
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── router/
│       ├── views/
│       ├── components/
│       ├── api/
│       └── utils/
├── requirements.txt
├── .env.example
└── README.md
```

---

## 4. 数据流

```
AKShare API ──┐
              ├→ data_fetcher.py ──→ PostgreSQL（主存储）
GoFundBot ────┘                     ↓
                                  Redis（缓存）
用户请求 ──→ FastAPI 路由 ──→ 业务服务层 ──→ 返回 JSON
                                      ↓
                                  Vue3 前端 ──→ ECharts 渲染
```

---

## 5. 数据库模型

### funds（基金基本信息）
```sql
CREATE TABLE funds (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(20),
    company VARCHAR(50),
    manager VARCHAR(50),
    establish_date DATE,
    scale DECIMAL(12,2),
    fee_buy DECIMAL(5,4),
    fee_sell DECIMAL(5,4),
    fee_manage DECIMAL(5,4),
    updated_at TIMESTAMP
);
```

### nav_history（基金净值历史）
```sql
CREATE TABLE nav_history (
    code VARCHAR(10),
    date DATE,
    nav DECIMAL(10,4),
    acc_nav DECIMAL(10,4),
    growth DECIMAL(8,4),
    PRIMARY KEY (code, date)
);
```

### fund_rankings（基金排行快照）
```sql
CREATE TABLE fund_rankings (
    code VARCHAR(10),
    rank_date DATE,
    type VARCHAR(20),
    rank_3m INT,
    rank_6m INT,
    rank_1y INT,
    rank_3y INT,
    total_count INT,
    PRIMARY KEY (code, rank_date)
);
```

### user_funds（用户收藏/持仓）
```sql
CREATE TABLE user_funds (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10),
    action VARCHAR(20),
    buy_price DECIMAL(10,4),
    buy_date DATE,
    amount DECIMAL(12,2),
    created_at TIMESTAMP
);
```

### portfolios（基金组合）
```sql
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP
);
```

### portfolio_holdings（组合持仓）
```sql
CREATE TABLE portfolio_holdings (
    portfolio_id INT REFERENCES portfolios(id),
    code VARCHAR(10),
    weight DECIMAL(5,4),
    PRIMARY KEY (portfolio_id, code)
);
```

---

## 6. 核心模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| data_fetcher.py | 从 AKShare 拉数据，写入 PG | AKShare |
| cache_manager.py | Redis 缓存管理，控制过期时间 | Redis |
| fund_screener.py | 4433 真排名、高级筛选 | data_fetcher |
| backtester.py | 定投回测引擎（普通/均线/回撤加仓） | data_fetcher |
| risk_analyzer.py | 风险指标（夏普/Calmar/Sortino/回撤） | numpy |
| portfolio.py | 组合创建/分析/优化 | PyPortfolioOpt |
| report_gen.py | 一键生成基金诊断报告 | 上面所有模块 |
| daily_update.py | 每日定时更新基金数据 | APScheduler |
| gofundbot.py | 调用 GoFundBot API 获取估值/分析 | HTTP |

---

## 7. 分阶段实施计划

### 第一阶段：数据 + 筛选（核心基础）
1. 项目脚手架搭建（FastAPI + Vue3 + PG + Redis）
2. PostgreSQL 数据模型设计（基金表、净值表、类型表）
3. AKShare 数据采集 + 入库（定时任务）
4. Redis 缓存层
5. 基金搜索 API
6. 基金详情 API（收益/回撤/夏普/波动率）
7. 基金排行 API
8. 真正的 4433 同类百分位排名筛选
9. GoFundBot API 集成（实时估值）
10. Vue3 基金搜索/详情/排行/筛选页面

### 第二阶段：回测 + 组合
11. 定投回测引擎（普通定投）
12. 均线智能定投回测
13. 回撤加仓定投回测
14. 策略对比功能
15. 基金组合创建/保存
16. 组合收益/风险分析
17. PyPortfolioOpt 最优权重计算
18. Vue3 回测/组合页面

### 第三阶段：监控 + 报告
19. 持仓监控功能
20. 回撤/排名恶化提醒
21. 基金经理分析
22. AI 基金诊断报告生成
23. 一键导出分析报告
24. Vue3 监控/报告页面

---

## 8. 外部服务集成

### GoFundBot API
```
实时估值: GET /api/estimate/{code}
市场分析: GET /api/market/analysis
```

### PyPortfolioOpt
```
最优权重: 本地调用，不走API
有效前沿: 本地计算
```

### xalpha
```
回测引擎: 参考其逻辑，自己实现
```

---

## 9. 错误处理

```
- AKShare 请求失败 → 自动重试3次 → 返回缓存数据
- 数据缺失/异常 → 标记并跳过 → 记录日志
- API 限流 → Redis 限流中间件 → 返回 429
- 前端错误 → 统一错误提示组件
```

---

## 10. 测试策略

```
- 后端：pytest 单元测试（核心算法）+ 集成测试（API）
- 前端：Vitest 单元测试（组件）
- E2E：暂不考虑，手动验证
```
