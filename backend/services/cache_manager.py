import json
from typing import Any, Optional
from backend.redis_client import redis_client


async def cache_get(key: str) -> Optional[Any]:
    """从缓存获取数据"""
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    """设置缓存数据，默认 TTL 1小时"""
    await redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))


async def cache_delete(key: str) -> None:
    """删除缓存"""
    await redis_client.delete(key)


async def cache_exists(key: str) -> bool:
    """检查缓存是否存在"""
    return await redis_client.exists(key) > 0
