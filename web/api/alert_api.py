"""
========================================
Alert API - 告警路由
========================================
功能: 告警规则 CRUD、历史、时间线、SSE 事件流
 作者: 上古必斩必杀
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from web.intelligence.alert_manager import alert_manager
from web.sse import EventBroadcaster, sse_format

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/alerts")
async def api_get_alerts():
    """获取所有告警规则（附带每个规则的事件统计）"""
    alerts = alert_manager.get_all_alerts()
    stats = alert_manager.alert_stats()
    return {
        "alerts": [
            {
                **a.to_dict(),
                "event_count": stats.get(a.id, {}).get("event_count", 0),
                "last_triggered_at": stats.get(a.id, {}).get("last_triggered_at"),
            }
            for a in alerts
        ]
    }


@router.post("/api/alerts")
async def api_create_alert(request: Request):
    """创建新的告警规则"""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001 - 非法 JSON 统一按 400 处理
        raise HTTPException(status_code=400, detail="请求体不是合法 JSON")
    keyword = body.get("keyword", "").strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="关键词不能为空")

    try:
        alert = alert_manager.add_alert(keyword)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 广播规则变更，其他标签页收到后同步刷新
    request.app.state.alert_broadcaster.publish({"type": "alert_updated"})
    return {"alert": alert.to_dict()}


@router.delete("/api/alerts/{alert_id}")
async def api_delete_alert(alert_id: str, request: Request):
    """删除告警规则"""
    deleted = alert_manager.remove_alert(alert_id)
    if deleted:
        request.app.state.alert_broadcaster.publish({"type": "alert_updated"})
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="告警规则不存在")


@router.post("/api/alerts/{alert_id}/toggle")
async def api_toggle_alert(alert_id: str, request: Request):
    """切换告警启用/禁用状态"""
    success = alert_manager.toggle_alert(alert_id)
    if success:
        request.app.state.alert_broadcaster.publish({"type": "alert_updated"})
        alerts = alert_manager.get_all_alerts()
        alert = next((a for a in alerts if a.id == alert_id), None)
        return {"alert": alert.to_dict() if alert else None}
    raise HTTPException(status_code=404, detail="告警规则不存在")


@router.get("/api/alerts/history")
async def api_get_alert_history(limit: int = 50):
    """获取告警历史记录"""
    history = alert_manager.get_history(limit)
    return {"history": [h.to_dict() for h in history]}


@router.delete("/api/alerts/history/all")
async def api_clear_alert_history_all():
    """清空告警历史"""
    alert_manager.clear_history()
    return {"cleared": True}


@router.get("/api/alerts/timeline/{keyword}")
async def api_get_alert_timeline(keyword: str):
    """获取关键词的事件时间线"""
    timeline = alert_manager.get_timeline(keyword)
    return {"keyword": keyword, "timeline": [h.to_dict() for h in timeline]}


@router.get("/api/alerts/stream")
async def api_alerts_stream(request: Request):
    """
    告警事件流 - SSE

    每个连接持有独立订阅队列，事件通过广播器 fan-out 给所有客户端
    """
    broadcaster: EventBroadcaster = request.app.state.alert_broadcaster
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    # 队列事件已是完整消息(如 {"type": "alert", "event": {...}} 或
                    # {"type": "alert_updated"}),原样转发,避免二次包装导致前端取不到字段
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