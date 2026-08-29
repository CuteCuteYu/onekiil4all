"""
========================================
Intelligence API - 热点资讯路由
========================================
功能: 热点资讯与关键词关联分析
（告警/RSS 路由见 alert_api.py 与 rss_api.py）
 作者: 上古必斩必杀
"""

import asyncio
import logging

from fastapi import APIRouter

from web.intelligence.trends import get_keyword_associations, get_trends

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/trends")
async def api_get_trends():
    """获取热门搜索和情报信息"""
    return await asyncio.to_thread(get_trends)


@router.get("/api/trends/associations")
async def api_get_keyword_associations(keyword: str):
    """获取指定关键词的关联分析"""
    if not keyword or len(keyword.strip()) < 2:
        return {"error": "关键词至少2个字符", "keyword": keyword, "associations": []}

    return await asyncio.to_thread(get_keyword_associations, keyword.strip())