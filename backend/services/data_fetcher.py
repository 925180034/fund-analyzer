import akshare as ak
import pandas as pd
from datetime import date, datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def fetch_fund_list() -> pd.DataFrame:
    """获取基金列表"""
    try:
        df = ak.fund_open_fund_info_em()
        # 统一列名
        df = df.rename(columns={
            "基金代码": "code",
            "基金简称": "name",
            "基金类型": "type",
        })
        return df[["code", "name", "type"]]
    except Exception as e:
        logger.error(f"获取基金列表失败: {e}")
        return pd.DataFrame()


async def fetch_fund_nav(code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """获取基金净值历史数据"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        df = df.rename(columns={
            "净值日期": "date",
            "单位净值": "nav",
            "日增长率": "growth",
        })
        df["code"] = code
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["acc_nav"] = None  # 累计净值需另外获取

        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date).date()]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date).date()]

        return df[["code", "date", "nav", "acc_nav", "growth"]]
    except Exception as e:
        logger.error(f"获取基金 {code} 净值失败: {e}")
        return pd.DataFrame()


async def fetch_fund_info(code: str) -> dict:
    """获取基金基本信息"""
    try:
        # 获取基金概况
        df = ak.fund_individual_basic_info_xq(symbol=code)
        info = dict(zip(df["item"], df["value"]))

        result = {
            "code": code,
            "name": info.get("基金名称", ""),
            "type": info.get("基金类型", ""),
            "company": info.get("基金管理人", ""),
            "manager": info.get("基金经理", ""),
            "establish_date": info.get("成立日期", None),
            "scale": float(info.get("资产规模", "0").replace("亿元", "").strip()) if info.get("资产规模") else None,
            "fee_buy": None,
            "fee_sell": None,
            "fee_manage": None,
        }
        return result
    except Exception as e:
        logger.error(f"获取基金 {code} 信息失败: {e}")
        return {"code": code, "error": str(e)}


async def fetch_fund_ranking(fund_type: str = "全部") -> pd.DataFrame:
    """获取基金排行数据"""
    try:
        df = ak.fund_open_fund_rank_em(symbol=fund_type)
        df = df.rename(columns={
            "基金代码": "code",
            "基金简称": "name",
        })
        return df
    except Exception as e:
        logger.error(f"获取基金排行失败: {e}")
        return pd.DataFrame()
