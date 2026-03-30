"""
对话管理模块
负责对话线程的管理
"""

from web.chat_handler import chat_handler
from web.todo_manager import TodoManager


def new_chat():
    """创建新对话"""
    chat_handler.reset_thread()
    print(f"新对话已创建 (thread_id: {chat_handler.current_thread_id})")


def get_thread_id() -> str:
    """获取当前对话线程 ID"""
    return chat_handler.current_thread_id


def get_todo_manager() -> TodoManager:
    """获取当前对话的 TODO 管理器"""
    return TodoManager(get_thread_id())


def create_todo_for_request(user_request: str) -> list[str]:
    """
    为用户请求创建 TODO 列表

    Args:
        user_request: 用户请求

    Returns:
        TODO 列表项
    """
    todo_mgr = get_todo_manager()
    todos = todo_mgr.create_todo(user_request)

    # 显示创建的 TODO 列表
    if todos:
        todo_mgr.display_todo("已创建任务清单")

    return todos
