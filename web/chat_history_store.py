"""
========================================
Chat History Store - 对话历史存储模块
========================================
功能: 基于 JSONL 追加写入的对话历史存储，
每条消息只追加一行，避免全量重写整个会话文件
 作者: CuteCuteYu
"""

import json
import logging
import re
import threading
from datetime import UTC, datetime
from pathlib import Path

from web.paths import CHAT_HISTORY_DIR

logger = logging.getLogger(__name__)

# 线程ID只允许安全字符，防止路径穿越
_SAFE_THREAD_ID = re.compile(r"^[A-Za-z0-9_-]+$")

# 多线程追加写入的文件锁
_write_lock = threading.Lock()


def _file_for(thread_id: str) -> Path:
    """
    获取线程对应的历史文件路径

    参数:
        thread_id: 线程ID

    返回:
        chat_history/{thread_id}.jsonl 的 Path

    异常:
        ValueError: 线程ID包含不安全字符
    """
    if not thread_id or not _SAFE_THREAD_ID.match(thread_id):
        raise ValueError(f"非法的线程ID: {thread_id!r}")
    return CHAT_HISTORY_DIR / f"{thread_id}.jsonl"


def append_message(
    thread_id: str, role: str, content: str, metadata: dict | None = None
):
    """
    追加一条消息到历史文件（首条消息时创建文件并写入会话头）

    参数:
        thread_id: 线程ID
        role: 消息角色 (user/assistant)
        content: 消息内容
        metadata: 可选的元数据
    """
    history_file = _file_for(thread_id)

    message: dict = {
        "type": "message",
        "role": role,
        "content": content,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if metadata is not None:
        message["metadata"] = metadata

    with _write_lock:
        CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        is_new = not history_file.exists() or history_file.stat().st_size == 0
        with open(history_file, "a", encoding="utf-8") as f:
            if is_new:
                header = {
                    "type": "session",
                    "thread_id": thread_id,
                    "created_at": datetime.now(UTC).isoformat(),
                }
                f.write(json.dumps(header, ensure_ascii=False) + "\n")
            f.write(json.dumps(message, ensure_ascii=False) + "\n")


def list_sessions() -> list[dict]:
    """
    列出所有历史会话

    返回:
        会话摘要列表，每项包含 thread_id、created_at、last_message
    """
    history: list[dict] = []

    if not CHAT_HISTORY_DIR.exists():
        return history

    for file in CHAT_HISTORY_DIR.glob("*.jsonl"):
        try:
            record = _summarize_file(file)
            if record:
                history.append(record)
        except OSError:
            logger.debug("历史文件读取失败: %s", file, exc_info=True)
            continue

    return sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)


def load_thread(thread_id: str) -> dict | None:
    """
    加载指定会话的完整历史

    参数:
        thread_id: 线程ID

    返回:
        {"thread_id", "created_at", "messages": [...]}，
        会话不存在时返回 None
    """
    history_file = _file_for(thread_id)
    if not history_file.exists():
        return None

    data: dict = {"thread_id": thread_id, "created_at": None, "messages": []}

    for line in history_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        if record.get("type") == "session":
            data["created_at"] = record.get("created_at")
        elif record.get("type") == "message":
            data["messages"].append(record)

    return data


def delete_thread(thread_id: str) -> bool:
    """
    删除指定会话的历史文件

    返回:
        文件存在并删除返回 True，否则 False
    """
    history_file = _file_for(thread_id)
    if history_file.exists():
        history_file.unlink()
        return True
    return False


def _summarize_file(file: Path) -> dict | None:
    """读取单个历史文件，生成会话摘要"""
    created_at = None
    last_message = ""

    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        if record.get("type") == "session":
            created_at = record.get("created_at")
        elif record.get("type") == "message" and record.get("content"):
            last_message = record["content"][:100]

    return {
        "thread_id": file.stem,
        "created_at": created_at,
        "last_message": last_message,
    }
