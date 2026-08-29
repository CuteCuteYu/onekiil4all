"""
========================================
Task Prompts - 任务分析提示词模块
========================================
功能: 构建任务完成状态检查的 AI 提示词
 作者: CuteCuteYu
"""


def build_efficient_update_prompt(
    tasks: list[dict], response: str, last_action: str
) -> str:
    """构建高效更新任务状态的提示词（返回已完成任务编号列表）"""
    task_descriptions = "\n".join(
        [f"{i + 1}. {t['description']}" for i, t in enumerate(tasks)]
    )
    completed_tasks = [t["description"] for t in tasks if t.get("completed", False)]
    completed_str = "\n".join(completed_tasks) if completed_tasks else "无"

    return f"""快速更新任务状态。基于以下信息，标记哪些任务已完成：

当前任务：
{task_descriptions}

AI最新响应摘要：{response[:300]}

最后操作：{last_action[:100]}

已标记完成的任务：
{completed_str}

请只返回数字列表，表示已完成的任务编号（从1开始）。
例如：如果任务1和3已完成，返回：[1, 3]
如果没有新任务完成，返回：[]
只返回列表，不要其他内容。"""