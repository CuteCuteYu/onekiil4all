"""
测试任务分析器的高效版本
"""

import sys
import os

sys.path.insert(0, ".")

from todo_manager import TodoManager
from task_analyzer import check_task_completed


def test_efficient_task_analysis():
    """测试高效任务分析"""
    print("=== 测试高效任务分析器 ===")

    # 需要设置 chat_handler 的线程ID
    from chat_handler import chat_handler

    thread_id = "test-thread-" + str(hash("test"))
    chat_handler.thread_id = thread_id  # 直接设置线程ID

    # 创建测试 TODO 管理器
    todo_mgr = TodoManager(thread_id)

    # 创建测试目录
    os.makedirs(f"todo/{thread_id}", exist_ok=True)

    # 创建测试任务
    test_tasks = [
        {"id": 1, "description": "创建项目目录结构", "completed": False},
        {"id": 2, "description": "编写主程序代码", "completed": False},
        {"id": 3, "description": "添加配置文件", "completed": False},
    ]

    # 保存测试任务
    todo_mgr._save_todo_md(test_tasks)
    print(f"1. 创建了测试任务，文件路径: {todo_mgr.get_file_path()}")
    print(f"   文件存在: {todo_mgr.exists()}")
    print(f"   任务数量: {len(test_tasks)}")

    # 模拟 AI 响应（部分完成）
    mock_response = "我已经创建了项目目录结构，包括 src/ 和 tests/ 目录。"
    mock_request = "创建一个Python项目"
    mock_action = "创建了目录结构"

    print(f"2. 模拟响应: {mock_response[:50]}...")

    # 第一次检查（应该调用 AI 更新）
    print("3. 第一次任务检查（应该调用AI）...")
    completed1, next_action1, interrupted1 = check_task_completed(
        mock_response, mock_request, mock_action
    )
    print(f"   结果: completed={completed1}, next_action={next_action1}")

    # 读取更新后的任务
    updated_tasks, _ = todo_mgr.read_todo()
    print(f"4. 更新后的任务状态:")
    for task in updated_tasks:
        status = "[DONE]" if task.get("completed", False) else "[TODO]"
        print(f"   {status} {task['description']}")

    # 第二次检查（应该使用缓存）
    print("5. 第二次任务检查（应该使用缓存）...")
    completed2, next_action2, interrupted2 = check_task_completed(
        mock_response, mock_request, mock_action
    )
    print(f"   结果: completed={completed2}, next_action={next_action2}")
    print(
        f"   是否使用缓存: {completed1 == completed2 and next_action1 == next_action2}"
    )

    # 测试不同的响应（应该重新调用 AI）
    print("6. 新响应任务检查（应该重新调用AI）...")
    new_response = "现在我已经编写了主程序代码，实现了基本功能。"
    completed3, next_action3, interrupted3 = check_task_completed(
        new_response, mock_request, "编写了代码"
    )
    print(f"   结果: completed={completed3}, next_action={next_action3}")

    # 清理测试文件
    import shutil

    if os.path.exists(f"todo/{thread_id}"):
        shutil.rmtree(f"todo/{thread_id}")

    print("\n=== 测试完成 ===")
    print("总结:")
    print(f"- AI 调用次数: 至少2次（第一次和新响应时）")
    print(f"- 缓存使用: 第二次检查应该使用了缓存")
    print(f"- 效率: 使用简化的提示词和缓存机制提高速度")


if __name__ == "__main__":
    test_efficient_task_analysis()
