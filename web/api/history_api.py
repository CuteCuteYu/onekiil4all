"""
========================================
History API - 对话历史路由
========================================
功能: 对话历史列表、详情查询、删除
 作者: CuteCuteYu
"""

from fastapi import APIRouter, HTTPException

from web.chat_history_store import delete_thread, list_sessions, load_thread
from web.sessions import is_safe_thread_id, remove_session
from web.todo_manager import TodoManager

router = APIRouter()


@router.get("/api/history")
async def api_get_history():
    """
    获取所有聊天历史会话列表

    返回:
        历史会话列表，按创建时间倒序排列
    """
    return {"history": list_sessions()}


@router.get("/api/history/{thread_id}")
async def api_get_chat_history(thread_id: str):
    """
    获取指定会话的聊天历史详情

    参数:
        thread_id: 会话线程ID

    返回:
        包含该会话的所有消息
    """
    try:
        data = load_thread(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法的线程ID")
    if data is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return data


@router.delete("/api/history/{thread_id}")
async def api_delete_history(thread_id: str):
    """
    删除指定会话

    同时删除会话历史文件和对应的TODO目录

    参数:
        thread_id: 要删除的会话线程ID

    返回:
        删除结果
    """
    if not is_safe_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="非法的线程ID")

    deleted = delete_thread(thread_id)

    # 删除TODO目录
    todo_mgr = TodoManager(thread_id)
    if todo_mgr.exists():
        todo_mgr.delete_todo()
        deleted = True

    # 从会话字典中移除
    remove_session(thread_id)

    return {"deleted": deleted}