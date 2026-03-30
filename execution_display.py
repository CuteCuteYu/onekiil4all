"""
执行过程显示模块
负责打印详细的执行步骤和工具调用信息
"""


def print_execution_steps(messages, step_num: int = 1) -> int:
    """
    打印详细的执行步骤和工具调用信息

    Args:
        messages: 消息列表
        step_num: 起始步骤编号

    Returns:
        下一个步骤编号
    """
    for i, msg in enumerate(messages):
        if msg.type == 'ai':
            # 显示 AI 思考/响应
            if hasattr(msg, 'content') and msg.content:
                print(f"  [{step_num}] AI: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
                step_num += 1

            # 显示工具调用
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})
                    tool_id = tool_call.get('id', '')[:8]

                    print(f"  [{step_num}] 工具调用: {tool_name} (ID: {tool_id}...)")
                    if tool_args:
                        # 格式化显示参数
                        args_str = str(tool_args)
                        if len(args_str) > 150:
                            args_str = args_str[:150] + "..."
                        print(f"       参数: {args_str}")
                    step_num += 1

        elif msg.type == 'tool':
            # 显示工具结果
            tool_name = msg.name if hasattr(msg, 'name') else 'unknown'
            content = msg.content if hasattr(msg, 'content') else ''
            content_preview = content[:100] + '...' if len(content) > 100 else content

            print(f"  [{step_num}] 工具结果 ({tool_name}): {content_preview}")
            step_num += 1

    return step_num


def print_execution_stats(details: dict):
    """
    打印执行统计信息

    Args:
        details: 详情字典，包含 total_messages, tool_calls_made, tool_results
    """
    print(f"\n[统计] 总消息数: {details['total_messages']}")
    if details['tool_calls_made']:
        print(f"       工具调用: {len(details['tool_calls_made'])} 次")
        for tc in details['tool_calls_made']:
            print(f"         - {tc['name']} ({tc['id']}...)")
    if details['tool_results']:
        print(f"       工具结果: {len(details['tool_results'])} 个")
    print()
