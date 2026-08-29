"""
========================================
Todo Prompts - TODO 提示词构建模块
========================================
功能: 构建 TODO 创建与更新的 AI 提示词
 作者: CuteCuteYu
"""


def build_create_todo_prompt(user_request: str) -> str:
    """构建生成 TODO 清单的提示词"""
    return f"""基于以下用户请求，生成一个任务清单（TODO列表）。

用户请求: {user_request}

请以JSON格式返回任务清单：
{{
    "tasks": [
        {{"id": 1, "description": "任务描述", "completed": false}},
        {{"id": 2, "description": "任务描述", "completed": false}}
    ]
}}

要求：
1. 将任务分解为具体的、可执行的小步骤
2. 每个步骤应该是独立的、可以验证完成的
3. 按照逻辑顺序排列
4. 通常3-8个任务项比较合适

只返回JSON，不要其他内容。"""


def build_update_todo_prompt(
    tasks: list[dict], response: str, last_action: str = ""
) -> str:
    """构建更新 TODO 完成状态的提示词"""
    tasks_str = "\n".join([f"- {t['description']}" for t in tasks])
    completed_str = "\n".join(
        [f"- {t['description']}" for t in tasks if t["completed"]]
    )

    return f"""根据以下信息，更新任务清单的完成状态。

当前任务清单:
{tasks_str}

已完成:
{completed_str}

AI 最新响应: {response}

最后执行的操作: {last_action}

请以JSON格式返回更新后的任务清单：
{{
    "tasks": [
        {{"id": 1, "description": "任务描述", "completed": true/false}}
    ]
}}

判断标准：
1. 如果任务的明确目标已在响应中达成，标记为已完成
2. 如果任务的部分结果已呈现，也标记为已完成
3. 只更新已完成的任务，不要添加新任务

只返回JSON，不要其他内容。"""