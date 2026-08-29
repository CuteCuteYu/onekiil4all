"""
========================================
Chat Handler - 聊天处理模块
========================================
功能: 负责处理聊天请求和调用AI模型获取响应，
支持 token 级流式输出（astream_events）
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════════════
# 导入项目模块
# ═══════════════════════════════════════════════════════════════════════

import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agent_set import agent_set  # Agent模块
from execution_display import (
    print_execution_stats,
    print_execution_steps,
)  # 执行显示模块
from web.chat_history_store import load_thread

logger = logging.getLogger(__name__)


def create_agent():
    """
    创建Agent实例的工厂函数

    返回:
        配置好的Agent实例
    """
    return agent_set.create_agent()


# 创建全局Agent实例
agent = create_agent()


# ═══════════════════════════════════════════════════════════════════════
# ChatHandler 类 - 聊天处理器
# ═══════════════════════════════════════════════════════════════════════


class ChatHandler:
    """
    聊天处理器类

    负责管理对话线程、维护消息历史，
    并调用Agent处理用户请求
    """

    def __init__(self):
        """初始化聊天处理器"""
        self.thread_id = None  # 当前对话线程ID
        self.message_history: dict[str, list[Any]] = {}  # 消息历史字典，键为线程ID

    @property
    def current_thread_id(self) -> str:
        """
        获取当前对话线程ID

        如果尚未设置，则自动生成一个新的UUID

        返回:
            当前线程ID字符串
        """
        if self.thread_id is None:
            self.thread_id = str(uuid.uuid4())
        return self.thread_id

    def reset_thread(self):
        """
        重置对话线程

        生成新的线程ID并清理旧线程的历史消息
        """
        old_thread_id = self.thread_id
        self.thread_id = str(uuid.uuid4())
        if old_thread_id is not None:
            self.message_history.pop(old_thread_id, None)

    def _load_history(self, thread_id: str) -> list[Any]:
        """
        从持久化历史(JSONL)加载该线程的历史消息

        将存储的 user/assistant 记录转换为 LangChain 消息对象，
        保证多轮对话上下文在服务重启后仍能恢复。

        参数:
            thread_id: 线程ID

        返回:
            LangChain 消息列表，无历史时返回空列表
        """
        try:
            data = load_thread(thread_id)
            if data and data.get("messages"):
                return _jsonl_to_langchain_messages(data["messages"])
        except Exception:
            logger.warning("加载线程历史失败: %s", thread_id, exc_info=True)
        return []

    def chat(
        self, content: str, verbose: bool = True, history: list[Any] | None = None
    ) -> tuple[str, dict]:
        """
        执行聊天并返回响应和详细信息（同步，一次性返回）

        参数:
            content: 用户输入的内容
            verbose: 是否显示详细信息（默认True）
            history: 可选的历史消息列表

        返回:
            tuple: (响应内容字符串, 详情字典)
            - 详情字典包含: total_messages, tool_calls_made, tool_results
        """
        if verbose:
            logger.info("正在处理请求")

        thread_id = self.current_thread_id

        # 如果线程没有历史记录，初始化为空列表
        if thread_id not in self.message_history:
            self.message_history[thread_id] = []

        # 复制历史消息并添加当前用户消息
        messages = self.message_history[thread_id].copy()
        messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

        # 调用Agent处理请求
        result = agent.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        )

        # 更新消息历史
        self.message_history[thread_id] = list(result["messages"])

        details = self._extract_details(result["messages"])

        # 打印执行步骤和统计信息
        if verbose:
            print_execution_steps(result["messages"], 1)
            print_execution_stats(details)

        return self._final_response(result["messages"]), details

    async def chat_stream(self, content: str) -> AsyncIterator[dict]:
        """
        流式执行聊天，实时产出进度事件

        事件类型:
        - {"type": "segment_start"}: 一段新的AI回复文本开始
        - {"type": "token", "content": str}: AI回复文本增量
        - {"type": "tool_call", "name": str, "status": str}: 工具调用开始/完成
        - {"type": "final", "response": str, "details": dict}: 结束事件

        参数:
            content: 用户输入的内容
        """
        thread_id = self.current_thread_id

        # 如果线程没有历史记录，从持久化历史(JSONL)加载，保证多轮对话上下文
        if thread_id not in self.message_history or not self.message_history[thread_id]:
            self.message_history[thread_id] = self._load_history(thread_id)

        messages = self.message_history[thread_id].copy()
        messages.append({"role": "user", "content": content})
        config = {"configurable": {"thread_id": thread_id}}

        yield {"type": "segment_start"}

        async for event in agent.astream_events(
            {"messages": messages}, config=config, version="v2"
        ):
            event_type = event["event"]

            if event_type == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                text = _chunk_text(chunk)
                if text:
                    yield {"type": "token", "content": text}

            elif event_type == "on_tool_start":
                yield {
                    "type": "tool_call",
                    "name": event.get("name", "unknown"),
                    "status": "执行中...",
                }

            elif event_type == "on_tool_end":
                yield {
                    "type": "tool_call",
                    "name": event.get("name", "unknown"),
                    "status": "✓ 完成",
                }

        # 流结束后从检查点恢复完整消息列表
        result_messages: list[Any] = []
        try:
            state = await agent.aget_state(config)
            result_messages = list(state.values.get("messages", []))
        except Exception:
            logger.warning("获取Agent最终状态失败", exc_info=True)

        if result_messages:
            self.message_history[thread_id] = result_messages

        details = self._extract_details(result_messages)
        response = self._final_response(result_messages) if result_messages else ""

        yield {"type": "final", "response": response, "details": details}

    @staticmethod
    def _extract_details(messages: list[Any]) -> dict:
        """
        从消息列表提取工具调用与结果统计

        参数:
            messages: Agent产出的消息列表

        返回:
            详情字典: total_messages, tool_calls_made, tool_results
        """
        details: dict = {
            "total_messages": len(messages),
            "tool_calls_made": [],  # 记录调用的工具
            "tool_results": [],  # 记录工具执行结果
        }

        for msg in messages:
            # AI消息中的工具调用
            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    details["tool_calls_made"].append(
                        {
                            "name": tc.get("name"),
                            "id": tc.get("id", "")[:8],  # 只取ID前8位
                        }
                    )
            # 工具执行结果
            elif msg.type == "tool":
                details["tool_results"].append(
                    {
                        "name": msg.name if hasattr(msg, "name") else "unknown",
                        "content_length": len(msg.content)
                        if hasattr(msg, "content")
                        else 0,
                    }
                )

        return details

    @staticmethod
    def _final_response(messages: list[Any]) -> str:
        """
        从消息列表提取最终AI回复（最后一条有内容的AI消息）

        参数:
            messages: Agent产出的消息列表

        返回:
            回复文本
        """
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai" and msg.content:
                return content_to_text(msg.content)

        if messages:
            return content_to_text(messages[-1].content)
        return ""


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


def _chunk_text(chunk: Any) -> str:
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


def _jsonl_to_langchain_messages(records: list[dict]) -> list[Any]:
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


# ═══════════════════════════════════════════════════════════════════════
# 全局单例实例
# ═══════════════════════════════════════════════════════════════════════

# 创建全局聊天处理器实例，供其他模块使用
chat_handler = ChatHandler()
