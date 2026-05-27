import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GoFundBotClient:
    """GoFundBot API 客户端"""

    BASE_URL = "https://api.gofundbot.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """发送请求"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.request(
                method=method,
                url=f"{self.BASE_URL}{path}",
                params=params,
                json=json,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GoFundBot API 错误: {e.response.status_code} - {e.response.text}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"GoFundBot 请求失败: {e}")
            return {"error": str(e)}

    async def get_fund_info(self, code: str) -> Dict[str, Any]:
        """获取基金信息"""
        return await self._request("GET", f"/fund/{code}")

    async def get_fund_nav(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取基金净值"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self._request("GET", f"/fund/{code}/nav", params=params)

    async def get_fund_ranking(self, fund_type: str = "全部") -> Dict[str, Any]:
        """获取基金排行"""
        return await self._request("GET", "/fund/ranking", params={"type": fund_type})

    async def search_funds(self, keyword: str) -> Dict[str, Any]:
        """搜索基金"""
        return await self._request("GET", "/fund/search", params={"keyword": keyword})

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 全局客户端实例
gofundbot_client = GoFundBotClient()
