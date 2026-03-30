# AGENTS.md - Code Development Guidelines

This file provides guidelines for agentic coding agents working on this codebase.

---

## Project Overview

- **Project name**: onekiil4all
- **Type**: AI 联网搜索问答系统 (AI联网搜索助手)
- **Tech stack**: Python 3.11+, LangChain, 智谱 GLM-4.7, SearXNG, FastAPI
- **Package manager**: uv
- **Virtual environment**: .venv/

---

## Build Commands

### Environment Setup
```bash
# Install dependencies using uv
uv sync

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### Running the Application
```bash
# Main chat interface (interactive CLI)
python main.py

# Web server
python web_server.py

# Using uvicorn directly
uvicorn web_server:app --reload --port 8000
```

### Development Commands
```bash
# Run with uv
uv run python main.py
uv run python web_server.py
uv run uvicorn web_server:app --reload --port 8000

# Type checking (if mypy installed)
uv run mypy .

# Linting (if ruff installed)
uv run ruff check .
```

### Testing
This project currently has **no test suite**. If adding tests:
```bash
# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_file.py

# Run single test function
uv run pytest tests/test_file.py::test_function_name

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

---

## Code Style Guidelines

### General Principles

- **Language**: Chinese comments and docstrings are acceptable (project is Chinese)
- **Simplicity**: Prefer simple, readable code over clever one-liners
- **Modules**: Use clear module names, one primary responsibility per module
- **No TODO comments**: Fix issues directly or document in issues, not as TODO comments

### Imports

**Order** (separate with blank lines):
1. Standard library
2. Third-party libraries
3. Local project modules

```python
# Good
import os
import json
from pathlib import Path

import requests
from fastapi import FastAPI

from model_set import model_set
from agent_set import agent_set
```

**Avoid**:
- Wildcard imports (`from module import *`)
- Circular imports
- Import inside functions (unless necessary)

### Formatting

- **Line length**: Max 120 characters
- **Indentation**: 4 spaces (not tabs)
- **Blank lines**:
  - 2 blank lines between top-level definitions
  - 1 blank line between method definitions in a class
- **No trailing whitespace**

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | lowercase, snake_case | `chat_handler.py` |
| Classes | PascalCase | `TodoManager` |
| Functions | snake_case | `create_todo()` |
| Variables | snake_case | `user_input` |
| Constants | UPPER_SNAKE_CASE | `MAX_AUTO_ITERATIONS` |
| Private | prefix with `_` | `_internal_method()` |

### Type Annotations

- **Use type hints** for all function parameters and return values
- **Prefer explicit types** over `Any`

```python
# Good
def chat(self, content: str, verbose: bool = True) -> tuple[str, dict]:
    ...

# Good - simple types
def get_file_path(self) -> str:
    ...

# Avoid
def process(data):  # No type hints
    ...
```

### Docstrings

Use Google-style docstrings for public methods:

```python
def create_todo(self, user_request: str) -> list[str]:
    """
    创建 TODO 列表

    Args:
        user_request: 用户请求

    Returns:
        TODO 列表项
    """
    ...
```

### Error Handling

- **Use specific exceptions** rather than catching all exceptions
- **Log errors** with meaningful context
- **Fail gracefully**: Provide user-friendly error messages

```python
# Good
try:
    result = model.invoke(prompt)
    content = result.content
except Exception as e:
    print(f"[错误] AI 调用失败: {e}")
    return []

# Better - specific exception
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    print(f"[错误] JSON 解析失败: {e}")
    return {}
```

### Async/Await

- Use `async/await` for I/O-bound operations (HTTP requests, file I/O)
- Use regular functions for CPU-bound operations
- Be consistent within a module

### Class Structure

```python
class TodoManager:
    """TODO 管理器"""

    def __init__(self, thread_id: str):
        self.thread_id = thread_id

    def create_todo(self, user_request: str) -> list[str]:
        """创建 TODO 列表"""
        ...

    def _save_todo_md(self, tasks: list[dict]):
        """保存 TODO 为 Markdown 文件（内部方法）"""
        ...
```

### Constants

- Place constants at module level (top of file)
- Use descriptive names
- Group related constants

```python
# Maximum auto iteration checks
MAX_AUTO_ITERATIONS = 5

# TODO directory
TODO_DIR = "todo"
```

### String Formatting

- Use f-strings for simple interpolation
- Use `.format()` for complex cases

```python
# Good
print(f"[执行] 正在处理请求: {content}")
status = f"进度: [{completed}/{total}]"

# Good
result = "用户: {}, 状态: {}".format(username, status)
```

---

## Project Structure

```
onekiil4all/
├── main.py              # Main CLI entry point
├── web_server.py        # FastAPI web server
├── chat_handler.py      # Chat processing
├── conversation.py       # Conversation management
├── task_analyzer.py     # Task completion analysis
├── todo_manager.py      # TODO list management
├── execution_display.py # Execution display utilities
├── interrupt_monitor.py # Interrupt handling
├── agent_set/           # Agent configuration
├── model_set/           # Model configuration
├── prompt/              # Prompt templates
├── static/              # Web static files
└── todo/                # Runtime TODO files (gitignored)
```

---

## Common Patterns

### Global Singleton
```python
# chat_handler.py
chat_handler = ChatHandler()
```

### Property
```python
@property
def current_thread_id(self):
    """获取当前对话线程 ID"""
    if self.thread_id is None:
        import uuid
        self.thread_id = str(uuid.uuid4())
    return self.thread_id
```

---

## Git Conventions

- **Commits**: Use clear, concise messages describing what changed
- **Branches**: Feature branches for new functionality
- **Never commit**: secrets, credentials, .env files, .venv/, __pycache__/

---

## IDE Configuration

The project uses `.idea/` for IntelliJ/PyCharm. VS Code users should add `.vscode/` to `.gitignore`.
