"""
========================================
Todo Manager - 待办事项管理模块
========================================
功能: 负责TODO列表的创建、更新、读取和删除
作者: onekiil4all
"""

# ═══════════════════════════════════════════════════════════════
# 导入标准库和项目模块
# ═══════════════════════════════════════════════════════════════

import os
import json
from pathlib import Path
from model_set import model_set

# 获取AI模型实例
model = model_set.model

# TODO文件存储目录
TODO_DIR = "todo"


# ═══════════════════════════════════════════════════════════════
# TodoManager 类 - TODO管理器
# ═══════════════════════════════════════════════════════════════


class TodoManager:
    """
    TODO列表管理器

    负责在指定线程下创建、更新、读取和删除TODO任务
    TODO以Markdown格式存储在文件中
    """

    def __init__(self, thread_id: str):
        """
        初始化TODO管理器

        参数:
            thread_id: 线程ID，用于区分不同的对话会话
        """
        self.thread_id = thread_id
        self.todo_dir = Path(TODO_DIR) / thread_id  # TODO目录
        self.todo_file = self.todo_dir / "todo.md"  # TODO文件路径

    def create_todo(self, user_request: str) -> list[str]:
        """
        创建TODO列表

        根据用户请求，让AI生成任务清单

        参数:
            user_request: 用户请求内容

        返回:
            TODO列表项描述字符串列表
        """
        # 创建TODO目录
        self.todo_dir.mkdir(parents=True, exist_ok=True)

        # 构建生成TODO的提示词
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
            # 调用AI生成TODO
            result = model.invoke(prompt)
            content = result.content

            # 提取JSON部分（处理可能的代码块格式）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # 解析JSON
            data = json.loads(content)
            tasks = data.get("tasks", [])

            # 保存为Markdown文件
            self._save_todo_md(tasks)
            return [t.get("description", "") for t in tasks]
        except (json.JSONDecodeError, KeyError):
            # 失败时创建空TODO
            self._save_todo_md([])
            return []

    def _save_todo_md(self, tasks: list[dict]):
        """
        保存TODO为Markdown文件

        参数:
            tasks: 任务列表，每个任务包含 id, description, completed
        """
        # 构建文件头部
        content = f"# TODO 列表 - Thread: {self.thread_id}\n\n"
        content += f"## 任务清单\n\n"

        if not tasks:
            content += "> AI 正在分析任务，请稍后...\n"
        else:
            # 遍历任务，构建列表
            for task in tasks:
                # [+]表示已完成，[-]表示未完成
                status = "[+]" if task.get("completed", False) else "[-]"
                content += f"{status} {task.get('description', '')}\n"

        # 写入文件
        with open(self.todo_file, "w", encoding="utf-8") as f:
            f.write(content)

    def read_todo(self) -> tuple[list[dict], str]:
        """
        读取TODO列表

        返回:
            tuple: (任务列表, 文件原始内容)
            - 任务列表: 包含description和completed的字典列表
        """
        if not self.todo_file.exists():
            return [], ""

        # 读取文件内容
        with open(self.todo_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析Markdown文件
        tasks = []
        for line in content.split("\n"):
            line = line.strip()
            # [+]表示已完成
            if line.startswith("[+]"):
                tasks.append({"description": line[3:].strip(), "completed": True})
            # [-]表示未完成
            elif line.startswith("[-]"):
                tasks.append({"description": line[3:].strip(), "completed": False})

        return tasks, content

    def update_todo(
        self, response: str, last_action: str = ""
    ) -> tuple[list[dict], bool]:
        """
        更新TODO列表状态

        让AI根据最新响应判断哪些任务已完成

        参数:
            response: AI最新响应内容
            last_action: 最后执行的操作

        返回:
            tuple: (更新后的任务列表, 是否全部完成)
        """
        tasks, _ = self.read_todo()

        if not tasks:
            return tasks, False

        # 构建任务状态更新的提示词
        tasks_str = "\n".join([f"- {t['description']}" for t in tasks])
        completed_str = "\n".join(
            [f"- {t['description']}" for t in tasks if t["completed"]]
        )

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
            # 调用AI更新状态
            result = model.invoke(prompt)
            content = result.content

            # 提取JSON
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
        """删除TODO目录和文件"""
        if self.todo_dir.exists():
            import shutil

            shutil.rmtree(self.todo_dir)

    def exists(self) -> bool:
        """检查TODO文件是否存在"""
        return self.todo_file.exists()

    def get_file_path(self) -> str:
        """获取TODO文件路径"""
        return str(self.todo_file)

    def display_todo(self, title: str = "TODO 列表"):
        """
        在终端显示TODO内容

        参数:
            title: 显示标题
        """
        tasks, content = self.read_todo()

        if not tasks:
            return

        # 打印标题和分隔线
        print(f"\n[{title}]")
        print("-" * 50)

        # 统计完成情况
        completed_count = sum(1 for t in tasks if t.get("completed", False))
        total_count = len(tasks)
        progress = f"[{completed_count}/{total_count}]"

        print(f"进度: {progress}")

        # 逐个显示任务
        for i, task in enumerate(tasks, 1):
            status = "[+]" if task.get("completed", False) else "[-]"
            desc = task.get("description", "")
            print(f"  {i}. {status} {desc}")

        print("-" * 50)
