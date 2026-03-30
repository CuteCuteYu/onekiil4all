"""
TODO 管理模块
负责 TODO 列表的创建、更新和检查
"""
import os
import json
from pathlib import Path
from model_set import model_set

model = model_set.model

# TODO 目录
TODO_DIR = "todo"


class TodoManager:
    """TODO 管理器"""

    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.todo_dir = Path(TODO_DIR) / thread_id
        self.todo_file = self.todo_dir / "todo.md"

    def create_todo(self, user_request: str) -> list[str]:
        """
        创建 TODO 列表

        Args:
            user_request: 用户请求

        Returns:
            TODO 列表项
        """
        # 创建目录
        self.todo_dir.mkdir(parents=True, exist_ok=True)

        # 让 AI 生成 TODO 列表
        prompt = f"""基于以下用户请求，生成一个任务清单（TODO列表）。

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

        try:
            result = model.invoke(prompt)
            content = result.content

            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            tasks = data.get("tasks", [])

            # 保存为 Markdown 文件
            self._save_todo_md(tasks)
            return [t.get("description", "") for t in tasks]
        except (json.JSONDecodeError, KeyError):
            # 失败时创建空 TODO
            self._save_todo_md([])
            return []

    def _save_todo_md(self, tasks: list[dict]):
        """
        保存 TODO 为 Markdown 文件

        Args:
            tasks: 任务列表，每个任务包含 id, description, completed
        """
        content = f"# TODO 列表 - Thread: {self.thread_id}\n\n"
        content += f"## 任务清单\n\n"

        if not tasks:
            content += "> AI 正在分析任务，请稍后...\n"
        else:
            for task in tasks:
                status = "[x]" if task.get("completed", False) else "[ ]"
                content += f"{status} {task.get('description', '')}\n"

        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def read_todo(self) -> tuple[list[dict], str]:
        """
        读取 TODO 列表

        Returns:
            (任务列表, 文件内容)
        """
        if not self.todo_file.exists():
            return [], ""

        with open(self.todo_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析 Markdown 文件
        tasks = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('[x]'):
                tasks.append({"description": line[3:].strip(), "completed": True})
            elif line.startswith('[ ]'):
                tasks.append({"description": line[3:].strip(), "completed": False})

        return tasks, content

    def update_todo(self, response: str, last_action: str = "") -> tuple[list[dict], bool]:
        """
        更新 TODO 列表状态

        Args:
            response: AI 最新响应
            last_action: 最后执行的操作

        Returns:
            (更新后的任务列表, 是否全部完成)
        """
        tasks, _ = self.read_todo()

        if not tasks:
            return tasks, False

        # 让 AI 判断哪些任务已完成
        tasks_str = "\n".join([f"- {t['description']}" for t in tasks])
        completed_str = "\n".join([f"- {t['description']}" for t in tasks if t['completed']])

        prompt = f"""根据以下信息，更新任务清单的完成状态。

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

        try:
            result = model.invoke(prompt)
            content = result.content

            # 提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            updated_tasks = data.get("tasks", [])

            # 保存更新
            self._save_todo_md(updated_tasks)

            # 检查是否全部完成
            all_completed = all(t.get("completed", False) for t in updated_tasks)

            return updated_tasks, all_completed
        except (json.JSONDecodeError, KeyError):
            return tasks, False

    def delete_todo(self):
        """删除 TODO 目录和文件"""
        if self.todo_dir.exists():
            import shutil
            shutil.rmtree(self.todo_dir)

    def exists(self) -> bool:
        """检查 TODO 文件是否存在"""
        return self.todo_file.exists()

    def get_file_path(self) -> str:
        """获取 TODO 文件路径"""
        return str(self.todo_file)

    def display_todo(self, title: str = "TODO 列表"):
        """
        在终端显示 TODO 内容

        Args:
            title: 显示标题
        """
        tasks, content = self.read_todo()

        if not tasks:
            return

        print(f"\n[{title}]")
        print("-" * 50)

        # 统计完成情况
        completed_count = sum(1 for t in tasks if t.get("completed", False))
        total_count = len(tasks)
        progress = f"[{completed_count}/{total_count}]"

        print(f"进度: {progress}")

        for i, task in enumerate(tasks, 1):
            status = "[✓]" if task.get("completed", False) else "[ ]"
            desc = task.get("description", "")
            print(f"  {i}. {status} {desc}")

        print("-" * 50)
