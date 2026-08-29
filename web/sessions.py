"""
========================================
Sessions - 会话管理模块
========================================
功能: 管理聊天会话的创建与获取，
带数量上限避免长期运行内存无限增长
 作者: CuteCuteYu
"""

import re
import uuid

# 会话数量上限，超出后淘汰最早的会话
MAX_SESSIONS = 200

# 线程ID只允许安全字符（用于文件/目录名，防路径穿越）
_SAFE_THREAD_ID = re.compile(r"^[A-Za-z0-9_-]+$")

# 会话存储字典，键为线程ID，值为会话信息字典
sessions: dict[str, dict] = {}


def is_safe_thread_id(thread_id: str) -> bool:
    """
    检查线程ID是否只含安全字符

    参数:
        thread_id: 线程ID

    返回:
        安全返回 True
    """
    return bool(thread_id) and bool(_SAFE_THREAD_ID.match(thread_id))


def get_or_create_session(thread_id: str | None) -> dict:
    """
    获取或创建会话

    如果传入的thread_id已存在则返回对应会话，否则创建新会话

    参数:
        thread_id: 线程ID，如果为None则创建新的

    返回:
        会话信息字典，包含thread_id、last_thread_id、max_auto_iterations等
    """
    # 如果线程ID存在，直接返回对应会话
    if thread_id and thread_id in sessions:
        return sessions[thread_id]

    # 生成新的线程ID
    new_tid = thread_id or str(uuid.uuid4())

    # 创建新会话信息
    session = {
        "thread_id": new_tid,
        "last_thread_id": None,  # 上一个线程ID（用于判断是否首次消息）
        "max_auto_iterations": 5,  # 最大自动迭代次数
    }

    # 保存会话并淘汰超额的旧会话
    sessions[new_tid] = session
    _evict_overflow()

    return session


def remove_session(thread_id: str):
    """移除指定会话（删除历史时调用）"""
    sessions.pop(thread_id, None)


def _evict_overflow():
    """会话数量超限时淘汰最早的会话"""
    while len(sessions) > MAX_SESSIONS:
        oldest = next(iter(sessions))
        del sessions[oldest]
