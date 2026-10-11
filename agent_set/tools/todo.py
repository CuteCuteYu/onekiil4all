"""
========================================
Tools Todo - 任务清单工具
========================================
功能: 让 Agent 自己读取并更新当前会话的任务清单。
Agent 主动维护清单后，外层循环可直接依据本地文件判定完成度，
无需每轮再额外调用一次模型做"任务完成度分析"，节省一次 LLM 往返。
 作者: 上古必斩必杀
"""

from langchain_core.tools import tool

# 工具名常量：外层循环据此判断 Agent 是否已自行更新清单
TODO_TOOL_NAME = "update_todo"


def _format_progress(tasks: list[dict]) -> str:
    """将任务列表格式化为带编号和进度的文本"""
    lines = []
    done = 0
    for i, task in enumerate(tasks, 1):
        completed = bool(task.get("completed"))
        done += 1 if completed else 0
        status = "[+]" if completed else "[-]"
        lines.append(f"{status} {i}. {task.get('description', '')}")
    pending = [t.get("description", "") for t in tasks if not t.get("completed")]
    summary = f"进度 {done}/{len(tasks)}"
    summary += f"；下一项：{pending[0]}" if pending else "；全部完成"
    return summary + "\n" + "\n".join(lines)


@tool
def read_todo() -> str:
    """
    读取当前会话的任务清单（带编号）。

    在开始执行任务前调用一次，确认需要完成的步骤与编号；
    随后每完成一步，用相同编号调用 update_todo 标记完成。
    """
    try:
        # 延迟导入，避免 agent_set 与 web 层循环依赖
        from web.conversation import get_todo_manager

        tasks, _ = get_todo_manager().read_todo()
        if not tasks:
            return "当前没有任务清单，可直接完成任务并给出最终回答。"
        return _format_progress(tasks)
    except Exception as e:  # noqa: BLE001 - 工具约定：失败以错误字符串返回
        return f"[Error] 读取任务清单失败: {e}"


@tool
def update_todo(completed: str) -> str:
    """
    将任务清单中指定编号的任务标记为已完成（编号从 1 开始）。

    参数:
        completed: 已完成的任务编号，用逗号分隔，例如 "1,3"；
                   没有任务完成时传空字符串 ""。

    返回:
        更新后的任务清单与进度；当前无任务清单时返回提示
    """
    try:
        # 延迟导入，避免 agent_set 与 web 层循环依赖
        from web.conversation import get_todo_manager

        todo_mgr = get_todo_manager()
        tasks, _ = todo_mgr.read_todo()
        if not tasks:
            return "当前没有任务清单，无需更新。"

        indices: set[int] = set()
        for piece in completed.replace("，", ",").split(","):
            piece = piece.strip()
            if piece.isdigit():
                indices.add(int(piece))

        for i, task in enumerate(tasks):
            if (i + 1) in indices:
                task["completed"] = True

        todo_mgr.save_todo(tasks)
        return _format_progress(tasks)
    except Exception as e:  # noqa: BLE001 - 工具约定：失败以错误字符串返回
        return f"[Error] 更新任务清单失败: {e}"
