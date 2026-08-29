"""
========================================
RSS API - RSS订阅路由
========================================
功能: RSS订阅源 CRUD、文章查询、SSE 事件流
 作者: 上古必斩必杀
"""

import asyncio
import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from web.intelligence.rss_manager import rss_manager
from web.intelligence.rss_parser import fetch_rss_articles
from web.sse import EventBroadcaster, sse_format

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/rss")
async def api_get_rss():
    """获取所有RSS订阅源"""
    sources = rss_manager.get_all_sources()
    return {"sources": [asdict(s) for s in sources]}


@router.post("/api/rss")
async def api_create_rss(request: Request):
    """创建新的RSS订阅源（创建后立即抓取文章，前端无需手动刷新即可看到）"""
    body = await request.json()
    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL不能为空")

    name = body.get("name", "").strip()
    try:
        source = rss_manager.add_source(url, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 创建后立即抓取文章并保存，让前端添加后马上能看到内容
    articles = await asyncio.to_thread(fetch_rss_articles, url)
    await asyncio.to_thread(rss_manager.update_source, source.id, articles)

    return {"source": asdict(source)}


@router.delete("/api/rss/{source_id}")
async def api_delete_rss(source_id: str):
    """删除RSS订阅源"""
    if rss_manager.remove_source(source_id):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="RSS源不存在")


@router.post("/api/rss/{source_id}/toggle")
async def api_toggle_rss(source_id: str):
    """切换RSS源的启用/禁用状态"""
    source = rss_manager.toggle_source(source_id)
    if source:
        return {"source": asdict(source)}
    raise HTTPException(status_code=404, detail="RSS源不存在")


@router.get("/api/rss/articles")
async def api_get_rss_articles():
    """获取所有RSS源的最新文章"""
    sources = rss_manager.get_all_sources()
    articles = []
    for s in sources:
        for a in s.articles:
            articles.append({"source": s.name, **a})
    return {"articles": articles[:50]}


@router.get("/api/rss/stream")
async def api_rss_stream(request: Request):
    """RSS文章事件流 - SSE（按连接 fan-out）"""
    broadcaster: EventBroadcaster = request.app.state.rss_broadcaster
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    # 队列事件已是完整消息 {"type": "rss", "article": {...}},原样转发
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield sse_format(event)
                except TimeoutError:
                    yield sse_format({"type": "ping"})
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )