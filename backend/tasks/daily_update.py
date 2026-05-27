from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
import logging

from backend.database import AsyncSessionLocal
from backend.models import Fund, NavHistory, FundRanking
from backend.services.data_fetcher import fetch_fund_list, fetch_fund_nav, fetch_fund_info
from backend.services.cache_manager import cache_delete

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def update_fund_list():
    """更新基金列表"""
    logger.info("开始更新基金列表...")
    try:
        df = await fetch_fund_list()
        if df.empty:
            logger.warning("获取基金列表为空")
            return

        async with AsyncSessionLocal() as session:
            for _, row in df.iterrows():
                fund = await session.get(Fund, row["code"])
                if fund:
                    fund.name = row["name"]
                    fund.type = row["type"]
                else:
                    fund = Fund(
                        code=row["code"],
                        name=row["name"],
                        type=row["type"],
                    )
                    session.add(fund)

            await session.commit()
            logger.info(f"更新基金列表完成，共 {len(df)} 只基金")
    except Exception as e:
        logger.error(f"更新基金列表失败: {e}")


async def update_fund_nav():
    """更新基金净值数据"""
    logger.info("开始更新基金净值...")
    try:
        async with AsyncSessionLocal() as session:
            # 获取所有基金
            result = await session.execute(select(Fund))
            funds = result.scalars().all()

            today = date.today()
            updated_count = 0

            for fund in funds:
                try:
                    df = await fetch_fund_nav(fund.code)
                    if df.empty:
                        continue

                    for _, row in df.iterrows():
                        # 检查是否已存在
                        existing = await session.execute(
                            select(NavHistory).where(
                                NavHistory.code == fund.code,
                                NavHistory.date == row["date"],
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        nav = NavHistory(
                            code=fund.code,
                            date=row["date"],
                            nav=row["nav"],
                            acc_nav=row.get("acc_nav"),
                            growth=row.get("growth"),
                        )
                        session.add(nav)

                    updated_count += 1

                    # 每100只基金提交一次
                    if updated_count % 100 == 0:
                        await session.commit()
                        logger.info(f"已更新 {updated_count} 只基金净值")

                except Exception as e:
                    logger.error(f"更新基金 {fund.code} 净值失败: {e}")
                    continue

            await session.commit()
            logger.info(f"更新基金净值完成，共更新 {updated_count} 只基金")
    except Exception as e:
        logger.error(f"更新基金净值失败: {e}")


async def update_fund_info():
    """更新基金详细信息"""
    logger.info("开始更新基金信息...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Fund).where(Fund.company.is_(None)))
            funds = result.scalars().all()

            updated_count = 0
            for fund in funds[:100]:  # 每次更新100只
                try:
                    info = await fetch_fund_info(fund.code)
                    if "error" in info:
                        continue

                    fund.company = info.get("company")
                    fund.manager = info.get("manager")
                    fund.establish_date = info.get("establish_date")
                    fund.scale = info.get("scale")
                    updated_count += 1
                except Exception as e:
                    logger.error(f"更新基金 {fund.code} 信息失败: {e}")
                    continue

            await session.commit()
            logger.info(f"更新基金信息完成，共更新 {updated_count} 只基金")
    except Exception as e:
        logger.error(f"更新基金信息失败: {e}")


def setup_scheduler():
    """配置定时任务"""
    # 每天 18:00 更新基金列表
    scheduler.add_job(
        update_fund_list,
        CronTrigger(hour=18, minute=0),
        id="update_fund_list",
        replace_existing=True,
    )

    # 每天 19:00 更新基金净值
    scheduler.add_job(
        update_fund_nav,
        CronTrigger(hour=19, minute=0),
        id="update_fund_nav",
        replace_existing=True,
    )

    # 每天 20:00 更新基金信息
    scheduler.add_job(
        update_fund_info,
        CronTrigger(hour=20, minute=0),
        id="update_fund_info",
        replace_existing=True,
    )

    logger.info("定时任务配置完成")
