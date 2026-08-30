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
Note: tests import modules that require model credentials; `tests/conftest.py` sets a dummy `ANTHROPIC_AUTH_TOKEN` automatically.

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
│   ├── web_server.py         # Entry point (app assembly, lifespan, static)
│   ├── background_tasks.py   # Background loops (alert check / RSS fetch)
│   ├── chat_handler.py       # Chat processing (token streaming via astream_events)
│   ├── message_utils.py      # Message conversion utils
│   ├── conversation.py       # Session management
│   ├── task_analyzer.py      # Task analysis (completion check)
│   ├── task_cache.py         # Task status cache
│   ├── task_prompts.py       # Task analysis prompt builders
│   ├── todo_manager.py       # TODO management
│   ├── todo_prompts.py       # TODO prompt builders
│   ├── sessions.py           # Session store (bounded, thread-id validation)
│   ├── chat_history_store.py # Chat history (JSONL append)
│   ├── sse.py                # SSE formatting + per-connection broadcast
│   ├── paths.py              # Project path constants (anchored to repo root)
│   ├── api/                  # API routers (split by responsibility)
│   │   ├── chat_api.py       # Chat SSE streaming
│   │   ├── session_api.py    # Sessions / TODO query
│   │   ├── history_api.py    # Chat history CRUD
│   │   ├── meta_api.py       # Skills/tools routes
│   │   ├── intelligence_api.py # Trends / associations
│   │   ├── alert_api.py      # Alert rules / history / SSE
│   │   ├── rss_api.py        # RSS sources / articles / SSE
│   │   └── canvas_api.py     # Boards / graph / types / GraphRAG routes
│   └── intelligence/         # Intelligence module
│       ├── trends/           # Trending data package (split by responsibility)
│       │   ├── __init__.py   # Entry (get_trends + cache)
│       │   ├── parsers.py    # Platform parse pure functions
│       │   ├── fetchers.py   # Network fetching + concurrency
│       │   ├── keywords.py   # Chinese/English keyword extraction
│       │   └── associations.py # Keyword association analysis
│       ├── graph_board.py    # Board mgmt / graph CRUD / saved-check / GraphRAG search
│       ├── alert_manager.py  # Alert management
│       ├── alert_models.py   # Alert data models
│       ├── rss_manager.py    # RSS subscription store
│       └── rss_parser.py     # Shared RSS/Atom parsing
├── agent_set/                # Agent components
│   ├── agent_set.py          # Agent creation
│   ├── tools/                # Tool set package (split by responsibility)
│   │   ├── __init__.py       # Tool list export
│   │   ├── shell.py          # PowerShell command execution
│   │   ├── files.py          # File read/write
│   │   ├── search.py         # Web search + RSS fetch
│   │   └── graphrag.py       # graphrag_status + graphrag_query tools
│   └── skill_set.py          # Skill configuration
├── model_set/                # Model configuration
│   └── model_set.py          # DeepSeek model setup (fails fast without key)
├── static/                   # Frontend (HTML/CSS/JS)
│   ├── index.html           # Main page
│   ├── style.css            # Styles
│   ├── config.js            # Config and constants
│   ├── state.js             # Global state
│   ├── dom.js               # DOM cache
│   ├── utils.js             # Utilities (markdown render + DOMPurify)
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
│       ├── rss.js          # RSS subscription
│       └── security.js     # Security intelligence
├── tests/                    # pytest tests
├── data/                     # Runtime data storage (generated, gitignored)
├── prompt/                   # Agent prompts
├── chat_history/             # Conversation history (runtime, gitignored)
└── pyproject.toml            # Project config
```

---

## Key Configuration

- **Environment Variables**: `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY` (required), `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL` - Model config read from ANTHROPIC_* env vars
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

### Session Management (see `web/sessions.py`)
```python
sessions: dict[str, dict] = {}
MAX_SESSIONS = 200  # 超限淘汰最早会话


def get_or_create_session(thread_id: str | None) -> dict:
    if thread_id and thread_id in sessions:
        return sessions[thread_id]
    session = {"thread_id": thread_id or str(uuid.uuid4()), ...}
    sessions[session["thread_id"]] = session
    return session
```


### Alert Module Implementation Notes (see `web/intelligence/alert_manager.py`, `web/api/intelligence_api.py`, `static/intelligence/alerts.js`)

- **Thread safety**: `AlertManager` is shared by the background check thread (`alert_checker` in `web_server.py`) and the API event-loop thread. All state mutations (`add_alert`/`remove_alert`/`toggle_alert`/`clear_history`/event creation) are serialized under `self._lock`.
- **Two-phase `check_alerts`**: matching runs lock-free (keywords lowercased once, matches collected as `(event_type, alert, item)` tuples); event creation + history save runs inside the lock.
- **Per-rule stats**: `alert_manager.alert_stats()` aggregates `event_count` / `last_triggered_at` per rule; `GET /api/alerts` returns these fields directly so the frontend needs no extra request.
- **SSE events are single-layer**: broadcasters publish complete event messages (e.g. `{"type": "alert", "event": {...}}` or `{"type": "alert_updated"}`) and the `/api/alerts/stream` + `/api/rss/stream` endpoints forward the queue item **as-is**. Never re-wrap them in another envelope, or the frontend loses the `keyword`/`title` fields.
- **Cross-tab sync**: create/delete/toggle endpoints publish `{"type": "alert_updated"}`; frontends refresh the rule list on receipt.
- **Frontend conventions in `alerts.js`**: unread badge on the ALERTS tab (cleared when the tab is opened), new alerts are prepended to the history locally with a throttled (5s) full re-sync, and SSE reconnect (`onopen` after the first open) re-fetches rules + history to compensate missed events.
- **JS pitfall**: never put a line break right after `return` before the expression (ASI inserts a semicolon and the function silently returns `undefined`). Use `return ( ... );`. This bug once made the alert rule list render empty.
### Links / Association Analysis Notes (see `web/intelligence/trends.py`, `static/intelligence/links.js`)

- **Pipeline**: keyword → web search titles (`_web_search_titles`: DDGS first, Bing HTML fallback) → project LLM summarizes 5-12 keywords (`_associations_via_search`) → ranked scores via `_rank_score`.
- **LLM output parsing**: `_parse_keywords_from_llm` tries whole-text JSON first (list or `{"keywords": [...]}` object; other dict shapes are rejected), then extracts the first array literal from prose. Never accept arbitrary arrays inside non-keywords dicts.
- **Caching**: per-keyword 60s cache (`_assoc_cache`, locked); search + LLM calls are expensive.
- **Two-level fallback**:
  1. If the LLM call fails (content-moderation rejection, rate limit, timeout, unparseable output), `_associations_via_search` falls back to `_associations_from_titles` — extracting keywords directly from the already-fetched search titles (jieba Chinese segmentation + English words, stopword-filtered). This keeps person/place names (e.g. 伊朗, 特朗普) working even when the model refuses to answer.
  2. If search itself returns nothing, `_associations_from_trends` falls back to built-in trending data using Chinese-bigram matching units (`_chinese_bigrams` / `_keyword_units`).
- **Chinese keyword extraction**: `extract_keywords` now extracts both English words (`[a-zA-Z]{3,}` minus `_EN_STOPWORDS`) and Chinese words via jieba (`_extract_chinese_keywords`, with a 2-4 char sliding-window fallback if jieba is unavailable), filtered by `_ZH_STOPWORDS`. Chinese keywords no longer produce empty results.
- **Frontend**: clicking a result keyword POSTs to /api/alerts with duplicate-alert feedback; on success it switches to ALERTS and highlights the new rule via `highlightAlertItem`; load text is "正在搜索并分析相关关键词...".
### RSS Module Implementation Notes (see `web/intelligence/rss_parser.py`, `web/intelligence/rss_manager.py`, `web/api/intelligence_api.py`, `static/intelligence/rss.js`)

- **Formats**: `parse_feed` supports RSS 2.0 (`<rss>`), Atom (`<feed>`, with/without namespace) and RSS 1.0 RDF/XML (`<rdf:RDF>` root, items in the `http://purl.org/rss/1.0/` namespace, optional `dc:date`). Unknown roots return `[]`.
- **Immediate fetch on add**: `POST /api/rss` fetches articles synchronously (via `asyncio.to_thread`) right after creating the source and saves them, so the frontend's `loadRssArticles()` shows content immediately without waiting for the background `rss_checker` cycle. Fetch failure keeps the source with empty articles; the background task retries on its normal interval.
- **Background updates**: `check_rss_sources` in `web_server.py` runs every `RSS_CHECK_INTERVAL` (default 10s), fetches only sources whose `fetch_interval` has elapsed, and pushes new articles via the `/api/rss/stream` SSE broadcaster (single-layer events, never re-wrapped).
- **Frontend**: `addRssSource` POSTs then calls `loadRssSources()` + `loadRssArticles()`; `startRssStream` consumes SSE and re-fetches articles on new events.
### Dev Server Notes (see `web/web_server.py`)

- **Graceful shutdown timeout**: `uvicorn.run(..., timeout_graceful_shutdown=5)` force-exits the worker after 5s even with open SSE connections. Without it, `reload=True` hot-reload hangs forever at "Waiting for connections to close" because the browser's SSE streams (`/api/rss/stream`, `/api/alerts/stream`) keep the old worker alive — every request then times out and the page spins. Never remove this timeout.
- **UTF-8 mode auto-restart**: on Windows, `__main__` re-execs itself with `-X utf8` when `sys.flags.utf8_mode` is off. Without it, deepagents' built-in `read_file` tool and `subprocess` output decoding fail with `UnicodeDecodeError` (GBK vs UTF-8), breaking the agent loop.
### Canvas / GraphRAG Board Integration Notes (see `web/intelligence/graph_board.py`, `web/api/canvas_api.py`, `agent_set/tools/graphrag.py`, `static/canvas.js`, `static/canvas.css`)

- **Single process-wide state**: `graph_board.py` holds module-level `graph_data` / `current_board` / `_lock` (same pattern as `alert_manager`). Board data lives in `data/graphs/*.json` (runtime data, gitignored, like `data/alerts.json`). Body errors use `GraphBoardError(status_code)` and `canvas_api.py` converts them to `HTTPException`.
- **API surface**: `/api/boards*`, `/api/graph`, `/api/graph/status`, `/api/types*`, `/api/node*`, `/api/edge`, `/api/save`, `/api/expand/{node_id}`, `/api/rag/context/{node_id}`. `GET /api/graph/status` returns `{board, has_board, saved, nodes, edges}` for the GraphRAG connection check.
- **Saved-state check**: `is_board_saved()` compares in-memory data with the board file via normalized JSON serialization (`sort_keys=True`); used by both the status endpoint and the agent tool.
- **Agent tools**: `graphrag_status` / `graphrag_query` are registered in `agent_set/tools/__init__.py` and always present. `graphrag_query` only performs a query when `is_board_saved()` is true; otherwise it returns a guidance string (never raises, compatible with `handle_tool_errors=False`). `search_graph` results are capped at `max_chars=6000` and ranked by name/type hits first. After a board switch the tools automatically follow the new current board (same global state); no agent restart needed.
- **Frontend**: `#tab-canvas` inside `.intelligence-content`; `static/canvas.js` + `static/canvas.css` restyled to the main app aesthetic (DM Mono, `--bg/--line/--fg*` vars). `init.js` calls `window.onCanvasTabShown()` when the CANVAS tab is activated (`cy.resize()` + `fit()` — the container is `display:none` at load). `refreshGraphRagStatus()` updates `#graphrag-badge` (chat header) and `#canvas-save-badge` (toolbar); it runs after every board/graph mutation and on a 5s interval only while the page is visible.
- **Gotchas**: only prevent the native context menu inside `#canvas-stage` (never globally — that would break the whole app). In `submitNode`, capture `wasEditing` before `resetNodeModal()` (which clears `editingNodeId`). Never start the dev server with a placeholder `ANTHROPIC_AUTH_TOKEN` (e.g. `dummy-for-smoke`) — it overrides real credentials and the model returns 401, so the agent says nothing; start with `uv run python -m web.web_server` to inherit the real env.
- **History**: the standalone GraphRAG Viz app has been removed after integration; board data was migrated to `data/graphs/`. Its original 2-hop RAG-context bug was fixed in the integrated `rag_context`.

### Agent Loop / Interrupt Handling Notes (see `web/api/chat_api.py`, `web/chat_handler.py`, `static/chat.js`, `agent_set/tools_set.py`)

- **Context history**: `chat_stream` loads prior user/assistant messages from the JSONL store (`_load_history` → `_jsonl_to_langchain_messages`) when the in-memory history is empty, so multi-turn context survives server restarts. Never `message_history.clear()` per request.
- **Loop stop reasons**: `stream_chat_response` emits a `loop_end` SSE event with `reason` (`completed` / `max_iterations` / `no_next_action` / `error`) and `iterations`; the frontend maps these to user-facing messages.
- **Interrupt handling**: the frontend shows a STOP button while the agent runs (aborts the fetch via `AbortController`). On the backend, `asyncio.CancelledError` is caught separately from `Exception` (it subclasses `BaseException`): partial responses are saved to history with `{"interrupted": True}`, TODO is preserved (task incomplete), and the error is re-raised. Never let an interrupt be swallowed by a generic `except Exception`.
- **Tool robustness**: `run_powershell` catches `TimeoutExpired`/`OSError` and returns `[Error]` strings instead of raising (deepagents runs with `handle_tool_errors=False`, so raised tool errors abort the whole loop). `read_text_file` auto-detects encoding (utf-8 → gbk → gb18030 → latin-1) when the requested encoding fails.
- **TODO archive**: on completion, `todo.md` is renamed to `todo_archive.md` (via `archive_todo`) instead of being deleted, preserving the task record.
- **JS pitfall**: `pendingQueue` in `chat.js` must be `$pendingQueue` (the DOM cache from `dom.js`); a bare `pendingQueue` throws `ReferenceError` in the `finally` block after an interrupt.
---
## Notes

- Test suite lives in `tests/` (run with `uv run pytest`)
- Use ruff for code quality checks
- Follow import order: stdlib → third-party → internal
- Keep docstrings concise but informative
- Use `logging` instead of `print` for server-side diagnostics
- ALERTS 前端渲染函数（`renderAlertItem` / `historyItemHtml`）的 `return` 必须紧跟表达式或使用括号换行，防止 ASI 陷阱
