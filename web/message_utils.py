"""
========================================
Message Utils - 消息转换工具模块
========================================
功能: 消息内容转换、流式文本提取、JSONL 历史转 LangChain 消息
 作者: CuteCuteYu
"""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage


def content_to_text(content: Any) -> str:
    """
    将消息 content 统一转为纯文本

    兼容两种模型返回格式：
    - OpenAI 风格: 纯字符串
    - Anthropic 风格: 内容块列表 [{"type": "text", "text": "..."}]

    参数:
        content: 消息 content 字段

    返回:
        拼接后的纯文本
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif (
                isinstance(block, dict)
                and block.get("type") in ("text", "output_text")
                and block.get("text")
            ):
                parts.append(block["text"])
        return "".join(parts)
    return ""


def chunk_text(chunk: Any) -> str:
    """
    提取流式消息块中的文本增量

    参数:
        chunk: AIMessageChunk 或类似对象

    返回:
        文本增量（无文本时为空字符串）
    """
    if chunk is None:
        return ""
    return content_to_text(getattr(chunk, "content", None))


def jsonl_to_langchain_messages(records: list[dict]) -> list[Any]:
    """
    将 JSONL 历史记录转换为 LangChain 消息列表

    只转换 user/assistant 角色消息，跳过会话头等元数据记录。

    参数:
        records: load_thread 返回的 messages 列表

    返回:
        LangChain 消息列表（HumanMessage / AIMessage）
    """
    messages: list[Any] = []
    for record in records:
        if record.get("type") != "message":
            continue
        role = record.get("role")
        content = record.get("content", "")
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages