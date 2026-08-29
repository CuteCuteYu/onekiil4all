"""
========================================
Session API - 会话与TODO路由
========================================
功能: 会话列表查询、TODO任务查询
 作者: CuteCuteYu
"""

from fastapi import APIRouter, HTTPException

from web.sessions import is_safe_thread_id, sessions
from web.todo_manager import TodoManager

router = APIRouter()


@router.get("/api/sessions")
async def api_list_sessions():
    """列出所有会话"""
    return {"sessions": list(sessions.keys())}


@router.get("/api/todo")
async def api_get_todo(thread_id: str):
    """
    获取当前TODO列表

    参数:
        thread_id: 线程ID

    返回:
        包含TODO任务列表、已完成数、总任务数等信息
    """
    if not is_safe_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="非法的线程ID")

    todo_mgr = TodoManager(thread_id)
    if not todo_mgr.exists():
        return {"exists": False}

    # 读取TODO任务
    tasks, _content = todo_mgr.read_todo()
    # 统计已完成任务数
    completed_count = sum(1 for t in tasks if t.get("completed", False))

    return {
        "exists": True,
        "tasks": tasks,
        "completed_count": completed_count,
        "total_count": len(tasks),
    }