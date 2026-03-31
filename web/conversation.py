"""
========================================
Conversation - 对话管理模块
========================================
功能: 负责对话线程的创建和管理
提供与ChatHandler和TodoManager的交互接口
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════
# 导入项目模块
# ═══════════════════════════════════════════════════════════════

from web.chat_handler import chat_handler
from web.todo_manager import TodoManager


# ═══════════════════════════════════════════════════════════════
# 对话管理函数
# ═══════════════════════════════════════════════════════════════


def new_chat():
    """
    创建新对话

    重置当前聊天处理器，创建新的线程ID
    """
    chat_handler.reset_thread()
    print(f"新对话已创建 (thread_id: {chat_handler.current_thread_id})")


def get_thread_id() -> str:
    """
    获取当前对话线程ID

    返回:
        当前线程ID字符串
    """
    return chat_handler.current_thread_id


def get_todo_manager() -> TodoManager:
    """
    获取当前对话的TODO管理器

    为当前线程创建或获取对应的TodoManager实例

    返回:
        TodoManager实例
    """
    return TodoManager(get_thread_id())


def create_todo_for_request(user_request: str) -> list[str]:
    """
    为用户请求创建TODO列表

    根据用户输入的内容，调用AI生成任务清单

    参数:
        user_request: 用户请求内容

    返回:
        TODO列表项描述字符串列表
    """
    # 获取当前线程的TODO管理器
    todo_mgr = get_todo_manager()

    # 调用AI生成TODO
    todos = todo_mgr.create_todo(user_request)

    # 显示创建的TODO列表
    if todos:
        todo_mgr.display_todo("已创建任务清单")

    return todos
