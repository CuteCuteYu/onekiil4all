"""
任务分析模块
负责检查任务完成状态
"""

from conversation import get_todo_manager


def check_task_completed(
    response: str, user_request: str, last_action: str = ""
) -> tuple[bool, str, bool]:
    """
    检查任务是否已完成（简化版，不调用 AI 检查）

    Args:
        response: 助手最新回复
        user_request: 用户原始请求
        last_action: 最后执行的操作

    Returns:
        (是否完成, 下一步指令或解释, 是否被用户打断)
    """
    print("\n[正在判断是否继续执行中...] (按 ESC 打断)")

    todo_mgr = get_todo_manager()
    tasks, todo_content = todo_mgr.read_todo()

    # 如果没有 TODO，默认已完成
    if not todo_mgr.exists() or not tasks:
        print("[检查] 无 TODO 任务，默认已完成")
        return True, "", False

    # 简化版：不再调用 AI 更新 TODO 状态
    # 只要存在未完成的 TODO，就认为未完成，返回让用户确认
    todo_mgr.display_todo("当前任务清单")
    print("[检查] 等待用户确认任务是否完成")

    return False, "", False
