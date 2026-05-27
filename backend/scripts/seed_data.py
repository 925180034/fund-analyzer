#!/usr/bin/env python3
"""
数据填充脚本 —— 从 AKShare 获取基金列表和净值历史，写入 PostgreSQL。
运行方式:  cd ~/fund-analyzer && python -m backend.scripts.seed_data
"""
import asyncio
import sys
import time
from datetime import datetime

import akshare as ak
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.database import AsyncSessionLocal, init_db
from backend.models.fund import Fund
from backend.models.nav import NavHistory

# ---------------------------------------------------------------------------
# 热门基金 —— 这些基金会额外拉取净值历史
# ---------------------------------------------------------------------------
HOT_FUNDS = ["110011", "005827", "161725", "000961", "003095", "163406", "005918", "012414"]

# ---------------------------------------------------------------------------
# 基金类型列表，用于从 ak.fund_open_fund_rank_em 获取分类数据
# ---------------------------------------------------------------------------
FUND_TYPES = ["股票型", "混合型", "债券型", "指数型", "QDII"]

BATCH_SIZE = 500  # 每批写入条数


# ===== 工具函数 =====

def _now():
    return datetime.now().strftime("%H:%M:%S")


def log(msg: str):
    print(f"[{_now()}] {msg}")


def _parse_fee(val) -> float | None:
    """把 '0.15%' 这类字符串转为 float，无法解析则返回 None。"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).replace("%", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ===== 1. 获取基金列表并写入 funds 表 =====

async def seed_funds():
    """从 AKShare 拉取各类型基金排行列表并写入 funds 表。"""
    log("========== 开始获取基金列表 ==========")
    total_inserted = 0

    async with AsyncSessionLocal() as session:
        for ftype in FUND_TYPES:
            log(f"正在获取 [{ftype}] 基金列表 ...")
            try:
                df = ak.fund_open_fund_rank_em(symbol=ftype)
            except Exception as e:
                log(f"  ⚠ 获取 [{ftype}] 失败: {e}")
                continue

            if df is None or df.empty:
                log(f"  ⚠ [{ftype}] 无数据")
                continue

            log(f"  获取到 {len(df)} 条 [{ftype}] 数据，开始写入 ...")

            rows = []
            for _, row in df.iterrows():
                fund_dict = {
                    "code": str(row.get("基金代码", "")).strip(),
                    "name": str(row.get("基金简称", "")).strip(),
                    "type": ftype,
                    "company": None,
                    "manager": None,
                    "establish_date": None,
                    "scale": None,
                    "fee_buy": _parse_fee(row.get("手续费")),
                    "fee_sell": None,
                    "fee_manage": None,
                }
                if fund_dict["code"]:
                    rows.append(fund_dict)

            # 分批 UPSERT 写入
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                stmt = pg_insert(Fund).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["code"],
                    set_={
                        "name": stmt.excluded.name,
                        "type": stmt.excluded.type,
                        "fee_buy": stmt.excluded.fee_buy,
                        "updated_at": datetime.now(),
                    },
                )
                await session.execute(stmt)
                await session.commit()
                total_inserted += len(batch)
                log(f"  [{ftype}] 已写入 {min(i + BATCH_SIZE, len(rows))}/{len(rows)} 条")

        log(f"基金列表写入完成，共处理 {total_inserted} 条记录。")


# ===== 2. 为热门基金获取净值历史并写入 nav_history 表 =====

async def seed_nav_history():
    """为热门基金获取净值历史并写入 nav_history 表。"""
    log("========== 开始获取热门基金净值历史 ==========")
    total_inserted = 0

    async with AsyncSessionLocal() as session:
        for idx, code in enumerate(HOT_FUNDS, 1):
            log(f"[{idx}/{len(HOT_FUNDS)}] 正在获取基金 {code} 的净值历史 ...")

            # --- 单位净值 ---
            try:
                df_nav = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            except Exception as e:
                log(f"  ⚠ 获取 {code} 单位净值失败: {e}")
                continue

            # --- 累计净值 ---
            try:
                df_acc = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
            except Exception as e:
                log(f"  ⚠ 获取 {code} 累计净值失败: {e}")
                df_acc = pd.DataFrame()

            if df_nav is None or df_nav.empty:
                log(f"  ⚠ 基金 {code} 无净值数据")
                continue

            # 合并累计净值
            if not df_acc.empty:
                df_acc = df_acc.rename(columns={"净值日期": "date_acc", "累计净值": "acc_nav"})
                df_acc["date_acc"] = pd.to_datetime(df_acc["date_acc"]).dt.date
                df_nav["_date"] = pd.to_datetime(df_nav["净值日期"]).dt.date
                merged = df_nav.merge(
                    df_acc[["date_acc", "acc_nav"]],
                    left_on="_date",
                    right_on="date_acc",
                    how="left",
                )
            else:
                merged = df_nav.copy()
                merged["_date"] = pd.to_datetime(merged["净值日期"]).dt.date
                merged["acc_nav"] = None

            rows = []
            for _, row in merged.iterrows():
                nav_dict = {
                    "code": code,
                    "date": row["_date"],
                    "nav": float(row["单位净值"]) if pd.notna(row.get("单位净值")) else None,
                    "acc_nav": float(row["acc_nav"]) if pd.notna(row.get("acc_nav")) else None,
                    "growth": float(row["日增长率"]) if pd.notna(row.get("日增长率")) else None,
                }
                rows.append(nav_dict)

            log(f"  基金 {code} 共 {len(rows)} 条净值记录，开始批量写入 ...")

            # 分批 UPSERT
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                stmt = pg_insert(NavHistory).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["code", "date"],
                    set_={
                        "nav": stmt.excluded.nav,
                        "acc_nav": stmt.excluded.acc_nav,
                        "growth": stmt.excluded.growth,
                    },
                )
                await session.execute(stmt)
                await session.commit()
                total_inserted += len(batch)

            log(f"  基金 {code} 写入完成 ({len(rows)} 条)")
            # 稍微休息一下，避免请求过快
            await asyncio.sleep(0.5)

        log(f"净值历史写入完成，共处理 {total_inserted} 条记录。")


# ===== 主入口 =====

async def main():
    log("====== Fund Analyzer 数据填充脚本 ======")
    start = time.time()

    # 1. 初始化数据库（创建表）
    log("正在初始化数据库表结构 ...")
    await init_db()
    log("数据库表结构就绪。")

    # 2. 填充基金列表
    await seed_funds()

    # 3. 填充热门基金净值历史
    await seed_nav_history()

    elapsed = time.time() - start
    log(f"====== 数据填充完成！总耗时: {elapsed:.1f}s ======")


if __name__ == "__main__":
    asyncio.run(main())
