"""
========================================
Execution Display - 执行过程显示模块
========================================
功能: 输出详细的执行步骤和工具调用信息
用于调试和了解AI Agent的执行过程
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════════════
# 导入模块
# ═══════════════════════════════════════════════════════════════════════

import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# 执行步骤打印函数
# ═══════════════════════════════════════════════════════════════════════


def print_execution_steps(messages, step_num: int = 1) -> int:
    """
    输出详细的执行步骤和工具调用信息

    遍历消息列表，逐个记录：
    - AI的思考/响应内容
    - 工具调用（名称、ID、参数）
    - 工具执行结果

    参数:
        messages: 消息列表（来自Agent执行结果）
        step_num: 起始步骤编号

    返回:
        下一个步骤编号（用于连续输出）
    """
    lines = []

    for _i, msg in enumerate(messages):
        if msg.type == "ai":
            # 显示AI思考/响应
            if hasattr(msg, "content") and msg.content:
                preview = (
                    f"{msg.content[:100]}{'...' if len(msg.content) > 100 else ''}"
                )
                lines.append(f"  [{step_num}] AI: {preview}")
                step_num += 1

            # 显示工具调用
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id", "")[:8]

                    lines.append(
                        f"  [{step_num}] 工具调用: {tool_name} (ID: {tool_id}...)"
                    )
                    if tool_args:
                        # 格式化显示参数
                        args_str = str(tool_args)
                        if len(args_str) > 150:
                            args_str = args_str[:150] + "..."
                        lines.append(f"       参数: {args_str}")
                    step_num += 1

        elif msg.type == "tool":
            # 显示工具结果
            tool_name = msg.name if hasattr(msg, "name") else "unknown"
            content = msg.content if hasattr(msg, "content") else ""
            content_preview = content[:100] + "..." if len(content) > 100 else content

            lines.append(f"  [{step_num}] 工具结果 ({tool_name}): {content_preview}")
            step_num += 1

    if lines:
        logger.debug("执行过程:\n%s", "\n".join(lines))

    return step_num


# ═══════════════════════════════════════════════════════════════════════
# 执行统计打印函数
# ═══════════════════════════════════════════════════════════════════════


def print_execution_stats(details: dict):
    """
    输出执行统计信息

    输出本次执行的总消息数、工具调用次数和工具结果数量

    参数:
        details: 详情字典，包含以下键:
        - total_messages: 总消息数
        - tool_calls_made: 工具调用列表
        - tool_results: 工具结果列表
    """
    lines = [f"[统计] 总消息数: {details['total_messages']}"]
    if details["tool_calls_made"]:
        lines.append(f"       工具调用: {len(details['tool_calls_made'])} 次")
        for tc in details["tool_calls_made"]:
            lines.append(f"         - {tc['name']} ({tc['id']}...)")
    if details["tool_results"]:
        lines.append(f"       工具结果: {len(details['tool_results'])} 个")
    logger.debug("\n".join(lines))
