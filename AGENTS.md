# AGENTS.md - Agent Coding Guidelines

This file provides guidelines for AI agents working on this codebase.

---

## Project Overview

- **Project Name**: 上古必斩必杀
- **Type**: AI Assistant Web Application
- **Tech Stack**: Python 3.11+, FastAPI, LangChain, LangGraph, DeepSeek
- **Architecture**: Agent-based with tool calling and auto-iteration

---

## Build/Lint/Test Commands

### Install Dependencies
```bash
uv sync
```

### Run Development Server
```bash
uv run python -m web.web_server
```
Then access `http://localhost:8000`

### Linting (Ruff)
```bash
uv run ruff check .
uv run ruff format .
```

### Run Single Test
```bash
uv run pytest tests/<test_file>::<test_class>::<test_method>
```
Note: This project currently has no test files.

---

## Code Style Guidelines

### Imports (ordered as in `agent_set/tools_set.py`)
```python
# 1. Standard library first
import subprocess
from pathlib import Path
import urllib.request

# 2. Third-party libraries
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# 3. Project internal modules
from web.chat_handler import chat_handler
```

### Type Annotations
- Use Python 3.11+ union syntax: `str | None` instead of `Optional[str]`
- Use built-in types: `list`, `dict`, `str`, `int`, `bool`

### Naming Conventions
- **Functions**: snake_case (`get_or_create_session`)
- **Classes**: PascalCase (`ChatHandler`, `TodoManager`)
- **Constants**: SCREAMING_SNAKE_CASE
- **Files**: snake_case (`web_server.py`, `chat_handler.py`)

### Functions and Tools
- Use `@tool` decorator from `langchain_core.tools` for tool functions
- Add docstrings to all public functions with Args and Return descriptions

### Error Handling
- For tool functions: return error messages as strings with `[Error]` prefix
- Example: `return f"[Error] 搜索失败: {e}"`

### File Operations
- Use `pathlib.Path` for file handling
- Always specify encoding: `encoding="utf-8"`
- Create parent directories: `filepath.parent.mkdir(parents=True, exist_ok=True)`

### API Development
- Use Pydantic `BaseModel` for request/response schemas
- Use `StreamingResponse` for SSE (Server-Sent Events)
- Follow RESTful conventions

### Frontend
- Native HTML/CSS/JavaScript (no frameworks)
- SSE for real-time updates
- Responsive design

---

## Project Structure

```
onekiil4all/
├── web/                      # FastAPI web server
│   ├── web_server.py         # Entry point
│   ├── chat_handler.py       # Chat processing
│   ├── conversation.py       # Session management
│   ├── task_analyzer.py     # Task analysis
│   ├── todo_manager.py      # TODO management
│   └── intelligence/         # Intelligence module
│       ├── trends.py        # Trending data
│       ├── alert_manager.py # Alert management
│       └── rss_manager.py   # RSS subscription
├── agent_set/                # Agent components
│   ├── agent_set.py          # Agent creation
│   ├── tools_set.py          # Tool definitions
│   └── skill_set.py          # Skill configuration
├── model_set/                # Model configuration
│   └── model_set.py          # DeepSeek model setup
├── static/                   # Frontend (HTML/CSS/JS)
│   ├── index.html           # Main page
│   ├── style.css            # Styles
│   ├── config.js            # Config and constants
│   ├── state.js             # State management
│   ├── dom.js               # DOM cache
│   ├── utils.js             # Utilities
│   ├── chat.js              # Chat functionality
│   ├── history.js           # History
│   ├── todo.js              # Todo items
│   ├── skills.js            # Skills/tools
│   ├── init.js              # Init and events
│   ├── alert.html           # Alert detail page
│   ├── alert.js             # Alert detail logic
│   ├── alert.css            # Alert detail styles
│   └── intelligence/        # Intelligence module
│       ├── trends.js       # Trending data
│       ├── alerts.js       # Alert functionality
│       ├── links.js        # Association search
│       └── rss.js          # RSS subscription
├── data/                     # Data storage (alerts.json, alert_history.json)
├── prompt/                   # Agent prompts
├── chat_history/             # Conversation history
└── pyproject.toml            # Project config
```

---

## Key Configuration

- **Environment Variables**: `DEEPSEEK_API_KEY` - Required for AI model access
- **TODO Auto-Creation**: Messages >= 20 characters trigger automatic TODO generation

---

## Common Patterns

### Tool Definition
```python
@tool
def tool_name(param: str) -> str:
    """Description of what the tool does."""
    try:
        return result
    except Exception as e:
        return f"[Error] {e}"
```

### Session Management
```python
sessions: dict[str, dict] = {}

def get_or_create_session(thread_id: str | None) -> dict:
    if thread_id and thread_id in sessions:
        return sessions[thread_id]
    return new_session()
```

---

## Notes

- No existing test suite - tests should be added
- Use ruff for code quality checks
- Follow import order: stdlib → third-party → internal
- Keep docstrings concise but informative
