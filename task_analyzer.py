"""
任务分析模块
负责检查任务完成状态和生成总结
"""
import json
from model_set import model_set
from interrupt_monitor import (
    start_interrupt_monitor,
    stop_interrupt_monitor,
    is_interrupted
)
from conversation import get_todo_manager

model = model_set.model


def check_task_completed(response: str, user_request: str, last_action: str = "") -> tuple[bool, str, bool]:
    """
    检查任务是否已完成（基于 TODO 列表）

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

    # 如果存在 TODO 文件，更新 TODO 状态
    if todo_mgr.exists():
        print("[检查] 正在更新 TODO 列表...")
        updated_tasks, all_completed = todo_mgr.update_todo(response, last_action)

        # 显示更新后的 TODO
        todo_mgr.display_todo("任务进度")

        if all_completed:
            # 全部完成，删除 TODO 并返回完成状态
            todo_mgr.display_todo("最终任务状态")
            todo_mgr.delete_todo()
            print("[完成] 所有任务已完成，TODO 列表已清除")
            return True, "所有任务已完成", False

        # 显示未完成的任务
        incomplete = [t['description'] for t in updated_tasks if not t.get('completed', False)]
        if incomplete:
            print(f"[待办] 还有 {len(incomplete)} 项任务未完成")

    # 构建 prompt，包含 TODO 信息
    todo_info = ""
    if tasks:
        tasks_str = "\n".join([f"- [{'x' if t.get('completed') else ' '}] {t['description']}" for t in tasks])
        todo_info = f"\n\n当前 TODO 列表:\n{tasks_str}\n\n请根据 TODO 列表的完成情况判断是否需要继续执行。"

    check_prompt = f"""分析以下对话，判断用户的原始需求是否已经完全满足。{todo_info}

用户原始请求: {user_request}

助手最新回复: {response}

请以JSON格式回复：
{{
    "completed": true/false,
    "reason": "完成状态的原因",
    "next_action": "如果未完成，下一步应该做什么（留空表示需要用户输入）"
}}

判断标准：
1. 如果用户的问题已得到直接回答 → completed: true
2. 如果任务已全部执行完成 → completed: true
3. 如果需要等待用户确认或输入 → completed: true（暂停等待用户）
4. 如果任务执行到一半但可以自动继续 → completed: false，并在next_action中说明下一步
5. 如果只是部分完成且需要更多信息 → completed: true（等待用户提供更多信息）

只返回JSON，不要其他内容。"""

    # 启动中断检测
    start_interrupt_monitor()

    try:
        check_result = model.invoke(check_prompt)

        # 检查是否被打断
        if is_interrupted():
            stop_interrupt_monitor()
            # 中断时保留 TODO 不删除
            return True, "[用户中断]", True

        # 尝试提取JSON内容
        content = check_result.content
        # 移除可能的markdown代码块标记
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        stop_interrupt_monitor()

        completed = data.get("completed", True)
        next_action = data.get("next_action", "")

        # 如果完成且存在 TODO，删除 TODO 并显示最终状态
        if completed and todo_mgr.exists():
            # 显示最终的 TODO 状态
            todo_mgr.display_todo("最终任务状态")
            todo_mgr.delete_todo()
            print("[完成] 任务已完成，TODO 列表已清除")

        return completed, next_action, False
    except (json.JSONDecodeError, KeyError, AttributeError):
        # JSON解析或数据提取失败时默认认为已完成，避免无限循环
        stop_interrupt_monitor()
        # 失败时也删除 TODO
        if todo_mgr.exists():
            todo_mgr.delete_todo()
            print("[完成] 任务已完成，TODO 列表已清除")
        return True, "", False


def generate_summary(user_request: str, final_response: str) -> tuple[str, bool]:
    """
    生成任务完成总结

    Args:
        user_request: 用户请求
        final_response: 最终响应

    Returns:
        (总结内容, 是否被用户打断)
    """
    print("[正在总结中...] (按 ESC 打断)")

    summary_prompt = f"""基于以下对话生成一个简洁的完成总结。

用户请求: {user_request}

最终响应: {final_response}

请用1-3句话总结：
1. 任务是否完成
2. 主要结果或结论
3. 任何需要注意的事项

保持简洁友好，不要重复响应中的详细内容。"""

    # 启动中断检测
    start_interrupt_monitor()

    try:
        summary_result = model.invoke(summary_prompt)

        # 检查是否被打断
        if is_interrupted():
            stop_interrupt_monitor()
            return "[总结已取消]", True

        stop_interrupt_monitor()
        return summary_result.content.strip(), False
    except Exception:
        stop_interrupt_monitor()
        return "", False
