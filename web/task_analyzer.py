"""
任务分析模块
负责检查任务完成状态（高效版）
"""

import time
from typing import Optional
from web.conversation import get_todo_manager

# 缓存最近的任务状态检查结果，避免重复调用 AI
_task_cache = {}
_CACHE_TIMEOUT = 30  # 缓存30秒


def check_task_completed(
    response: str, user_request: str, last_action: str = ""
) -> tuple[bool, str, bool]:
    """
    高效检查任务是否已完成，调用 AI 更新 TODO 状态

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

    # 调试信息
    print(f"[调试] TODO 文件存在: {todo_mgr.exists()}")
    print(f"[调试] 读取的任务数: {len(tasks)}")

    # 如果没有 TODO，默认已完成
    if not todo_mgr.exists() or not tasks:
        print("[检查] 无 TODO 任务，默认已完成")
        return True, "", False

    # 检查缓存
    cache_key = f"{todo_mgr.thread_id}:{hash(response[:100])}:{hash(last_action)}"
    current_time = time.time()

    if cache_key in _task_cache:
        cache_time, cached_result = _task_cache[cache_key]
        if current_time - cache_time < _CACHE_TIMEOUT:
            print("[检查] 使用缓存结果")
            return cached_result

    # 调用 AI 更新 TODO 状态
    print("[检查] 正在分析任务完成状态...")

    try:
        # 使用高效的提示词，让 AI 快速判断
        updated_tasks, all_completed = _efficient_update_todo(
            todo_mgr, response, last_action
        )

        # 显示更新后的 TODO
        todo_mgr.display_todo("当前进度")

        # 调试：打印任务状态
        completed_count = sum(1 for t in updated_tasks if t.get("completed", False))
        print(f"[调试] 完成任务: {completed_count}/{len(updated_tasks)}")

        # 生成下一步指令（如果需要）
        next_action = ""
        if not all_completed:
            next_action = _generate_next_action(updated_tasks, response, user_request)
            print(f"[检查] 下一步: {next_action[:80] if next_action else '(无)'}...")
        else:
            print("[检查] 所有任务已完成")

        result = (all_completed, next_action, False)

        # 缓存结果
        _task_cache[cache_key] = (current_time, result)

        # 清理过期缓存
        _clean_old_cache(current_time)

        return result

    except Exception as e:
        print(f"[检查] AI 分析失败，使用简化检查: {e}")
        # 失败时回退到简化检查
        return _fallback_check(todo_mgr, tasks)


def _efficient_update_todo(
    todo_mgr, response: str, last_action: str
) -> tuple[list[dict], bool]:
    """
    高效更新 TODO 状态，使用优化的提示词
    """
    from model_set import model_set

    tasks, _ = todo_mgr.read_todo()
    if not tasks:
        return [], True

    # 构建高效的提示词
    task_descriptions = "\n".join(
        [f"{i + 1}. {t['description']}" for i, t in enumerate(tasks)]
    )
    completed_tasks = [t["description"] for t in tasks if t.get("completed", False)]
    completed_str = "\n".join(completed_tasks) if completed_tasks else "无"

    prompt = f"""快速更新任务状态。基于以下信息，标记哪些任务已完成：

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

    try:
        # 使用较小的 max_tokens 加快响应
        result = model_set.model.invoke(prompt, max_tokens=50)
        content = result.content.strip()

        # 解析结果
        completed_indices = []
        if content.startswith("[") and content.endswith("]"):
            import ast

            try:
                completed_indices = ast.literal_eval(content)
            except:
                completed_indices = []

        # 更新任务状态
        for i, task in enumerate(tasks):
            task_id = i + 1
            if task_id in completed_indices:
                task["completed"] = True

        # 保存更新
        todo_mgr._save_todo_md(tasks)

        # 检查是否全部完成
        all_completed = all(t.get("completed", False) for t in tasks)

        return tasks, all_completed

    except Exception as e:
        print(f"[更新] 快速更新失败: {e}")
        # 回退到标准更新方法
        return todo_mgr.update_todo(response, last_action)


def _generate_next_action(tasks: list[dict], response: str, user_request: str) -> str:
    """
    生成下一步指令
    """
    # 找出第一个未完成的任务
    for task in tasks:
        if not task.get("completed", False):
            return f"继续执行: {task['description']}"

    # 所有任务都已完成，返回空字符串
    return ""


def _fallback_check(todo_mgr, tasks: list[dict]) -> tuple[bool, str, bool]:
    """
    简化检查（回退方案）
    """
    todo_mgr.display_todo("当前任务清单")

    # 检查是否有未完成的任务
    has_uncompleted = any(not t.get("completed", False) for t in tasks)

    if has_uncompleted:
        print("[检查] 检测到未完成任务，等待用户确认")
        return False, "", False
    else:
        print("[检查] 所有任务标记为已完成")
        return True, "", False


def _clean_old_cache(current_time: float):
    """
    清理过期缓存
    """
    global _task_cache
    expired_keys = [
        key
        for key, (cache_time, _) in _task_cache.items()
        if current_time - cache_time > _CACHE_TIMEOUT
    ]
    for key in expired_keys:
        del _task_cache[key]
    if expired_keys:
        print(f"[缓存] 清理了 {len(expired_keys)} 个过期缓存")
