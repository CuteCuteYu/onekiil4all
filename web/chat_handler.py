"""
聊天处理模块
负责处理聊天请求和响应
"""

from model_set import model_set
from agent_set import agent_set
from execution_display import print_execution_steps, print_execution_stats
from typing import List, Dict, Any

model = model_set.model


# 创建 agent 的函数
def create_agent():
    return agent_set.create_agent()


agent = create_agent()


class ChatHandler:
    """聊天处理器"""

    def __init__(self):
        self.thread_id = None
        self.message_history: Dict[str, List[Any]] = {}

    @property
    def current_thread_id(self):
        """获取当前对话线程 ID"""
        if self.thread_id is None:
            import uuid

            self.thread_id = str(uuid.uuid4())
        return self.thread_id

    def reset_thread(self):
        """重置对话线程"""
        import uuid

        self.thread_id = str(uuid.uuid4())
        if self.current_thread_id in self.message_history:
            del self.message_history[self.current_thread_id]

    def chat(
        self, content: str, verbose: bool = True, history: List[Any] = None
    ) -> tuple[str, dict]:
        """
        执行聊天并返回响应和详细信息

        Args:
            content: 用户输入内容
            verbose: 是否显示详细信息
            history: 可选的历史消息列表

        Returns:
            (响应内容, 详情字典)
        """
        if verbose:
            print(f"\n[执行] 正在处理请求...")

        thread_id = self.current_thread_id

        if thread_id not in self.message_history:
            self.message_history[thread_id] = []

        messages = self.message_history[thread_id].copy()
        messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

        result = agent.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}},
        )

        self.message_history[thread_id] = list(result["messages"])

        # 收集详细信息
        details = {
            "total_messages": len(result["messages"]),
            "tool_calls_made": [],
            "tool_results": [],
        }

        # 统计工具调用和结果
        for msg in result["messages"]:
            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    details["tool_calls_made"].append(
                        {
                            "name": tc.get("name"),
                            "id": tc.get("id", "")[:8],
                        }
                    )
            elif msg.type == "tool":
                details["tool_results"].append(
                    {
                        "name": msg.name if hasattr(msg, "name") else "unknown",
                        "content_length": len(msg.content)
                        if hasattr(msg, "content")
                        else 0,
                    }
                )

        # 打印执行步骤
        if verbose:
            print(f"[步骤] 执行过程:")
            print_execution_steps(result["messages"], 1)
            print_execution_stats(details)

        # 取最后一条 AI 消息作为回复（跳过 tool 消息）
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.type == "ai" and msg.content:
                return msg.content, details
        return result["messages"][-1].content, details


# 全局单例
chat_handler = ChatHandler()
