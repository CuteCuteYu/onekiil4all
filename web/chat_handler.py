"""
========================================
Chat Handler - 聊天处理模块
========================================
功能: 负责处理聊天请求和调用AI模型获取响应
作者: onekiil4all
"""

# ═══════════════════════════════════════════════════════════════
# 导入项目模块
# ═══════════════════════════════════════════════════════════════

from model_set import model_set  # AI模型模块
from agent_set import agent_set  # Agent模块
from execution_display import (
    print_execution_steps,
    print_execution_stats,
)  # 执行显示模块
from typing import List, Dict, Any  # 类型注解

# ═══════════════════════════════════════════════════════════════
# 初始化AI模型和Agent
# ═══════════════════════════════════════════════════════════════

# 获取AI模型实例
model = model_set.model


def create_agent():
    """
    创建Agent实例的工厂函数

    返回:
        配置好的Agent实例
    """
    return agent_set.create_agent()


# 创建全局Agent实例
agent = create_agent()


# ═══════════════════════════════════════════════════════════════
# ChatHandler 类 - 聊天处理器
# ═══════════════════════════════════════════════════════════════


class ChatHandler:
    """
    聊天处理器类

    负责管理对话线程、维护消息历史，
    并调用Agent处理用户请求
    """

    def __init__(self):
        """初始化聊天处理器"""
        self.thread_id = None  # 当前对话线程ID
        self.message_history: Dict[str, List[Any]] = {}  # 消息历史字典，键为线程ID

    @property
    def current_thread_id(self):
        """
        获取当前对话线程ID

        如果尚未设置，则自动生成一个新的UUID

        返回:
            当前线程ID字符串
        """
        if self.thread_id is None:
            import uuid

            self.thread_id = str(uuid.uuid4())
        return self.thread_id

    def reset_thread(self):
        """
        重置对话线程

        生成新的线程ID并清空该线程的历史消息
        """
        import uuid

        self.thread_id = str(uuid.uuid4())
        if self.current_thread_id in self.message_history:
            del self.message_history[self.current_thread_id]

    def chat(
        self, content: str, verbose: bool = True, history: List[Any] = None
    ) -> tuple[str, dict]:
        """
        执行聊天并返回响应和详细信息

        参数:
            content: 用户输入的内容
            verbose: 是否显示详细信息（默认True）
            history: 可选的历史消息列表

        返回:
            tuple: (响应内容字符串, 详情字典)
            - 详情字典包含: total_messages, tool_calls_made, tool_results
        """
        if verbose:
            print(f"\n[执行] 正在处理请求...")

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

        # ═══════════════════════════════════════════════════════════
        # 收集详细信息用于统计和显示
        # ═══════════════════════════════════════════════════════════
        details = {
            "total_messages": len(result["messages"]),
            "tool_calls_made": [],  # 记录调用的工具
            "tool_results": [],  # 记录工具执行结果
        }

        # 遍历所有消息，提取工具调用和结果
        for msg in result["messages"]:
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

        # 打印执行步骤和统计信息
        if verbose:
            print(f"[步骤] 执行过程:")
            print_execution_steps(result["messages"], 1)
            print_execution_stats(details)

        # 取最后一条AI消息作为回复（跳过tool消息）
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.type == "ai" and msg.content:
                return msg.content, details

        # 如果没有AI消息，返回最后一条消息
        return result["messages"][-1].content, details


# ═══════════════════════════════════════════════════════════════
# 全局单例实例
# ═══════════════════════════════════════════════════════════════

# 创建全局聊天处理器实例，供其他模块使用
chat_handler = ChatHandler()
