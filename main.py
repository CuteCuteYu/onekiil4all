"""
主程序入口
交互式聊天主循环
"""

from chat_handler import chat_handler
from conversation import (
    new_chat,
    create_todo_for_request,
    get_thread_id,
    get_todo_manager,
)
from task_analyzer import check_task_completed

# 最大自动迭代次数
MAX_AUTO_ITERATIONS = 5


def run_auto_iteration(
    current_request: str, response: str, last_action: str = ""
) -> tuple[int, bool, str]:
    """
    运行自动迭代检查和执行

    Args:
        current_request: 当前用户请求
        response: 当前响应
        last_action: 最后执行的操作

    Returns:
        (迭代次数, 是否被中断, 最后操作)
    """
    iteration = 0
    interrupted = False
    current_last_action = last_action

    while iteration < MAX_AUTO_ITERATIONS:
        completed, next_action, is_int = check_task_completed(
            response, current_request, current_last_action
        )

        if is_int:
            print("\n[已中断] 回到主循环")
            return iteration, True, current_last_action

        if completed:
            if next_action:
                print(f"\n[说明] {next_action}")
            todo_mgr = get_todo_manager()
            if todo_mgr.exists():
                todo_mgr.display_todo("任务完成")
                todo_mgr.delete_todo()
                print("[完成] TODO 列表已清除")
            break

        if next_action:
            print(f"\n[自动继续] {next_action}")
            # 使用下一步指令继续执行
            response, details = chat_handler.chat(next_action)
            print(f"\n助手: {response}")

            # 执行完后显示 TODO 进度
            todo_mgr = get_todo_manager()
            if todo_mgr.exists():
                todo_mgr.display_todo("当前进度")

            current_last_action = next_action
            iteration += 1
        else:
            break

    return iteration, False, current_last_action


def main():
    """主循环"""
    print("聊天已启动，输入 'quit'/'exit' 退出，'/new' 开始新对话")

    # 记录上一个 thread_id，用于检测新对话
    last_thread_id = None

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        if user_input.lower() == "/new":
            new_chat()
            last_thread_id = get_thread_id()
            continue

        current_thread_id = get_thread_id()

        # 检测是否是新对话的第一次输入
        is_first_message = last_thread_id != current_thread_id

        # 如果是新对话的第一次输入，创建 TODO 列表
        if is_first_message:
            print(f"\n[初始化] 正在为任务创建 TODO 列表...")
            todos = create_todo_for_request(user_input)
            if todos:
                print(f"[TODO] 已创建 {len(todos)} 项任务清单")
            last_thread_id = current_thread_id

        # 初始响应
        response, details = chat_handler.chat(user_input)
        print(f"\n助手: {response}")

        # 获取工具调用作为 last_action
        last_action = ""
        if details.get("tool_calls_made"):
            last_action = f"调用工具: {', '.join([tc['name'] for tc in details['tool_calls_made']])}"

        # 自动检查并继续执行
        iteration, interrupted, _ = run_auto_iteration(
            user_input, response, last_action
        )

        if iteration >= MAX_AUTO_ITERATIONS:
            print(
                f"\n[提示] 已达到最大自动执行次数({MAX_AUTO_ITERATIONS})，请确认是否需要继续。"
            )


if __name__ == "__main__":
    main()
