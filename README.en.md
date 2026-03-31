# 上古必斩必杀

AI Intelligent Assistant - Built with LangChain + DeepSeek

## Project Overview

上古必斩必杀 is a powerful AI assistant that supports:

- **Smart Conversation**: Based on DeepSeek large language model
- **Task Management**: Auto-generate and manage TODO lists
- **Tool Calling**: Support for multiple tools (file operations, command execution, etc.)
- **Web Interface**: Modern responsive frontend

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, **LangChain**, LangGraph
- **AI Model**: DeepSeek Chat API
- **Frontend**: Native HTML/CSS/JavaScript
- **Architecture**: Agent architecture with tool calling and auto-iteration
- **Reference**: LangChain, DeepAgents

## Project Structure

```
onekiil4all/
├── web/                      # Web server code
│   ├── web_server.py         # FastAPI web server
│   ├── chat_handler.py       # Chat handler
│   ├── conversation.py       # Conversation management
│   ├── task_analyzer.py      # Task analyzer
│   ├── todo_manager.py       # TODO manager
│   ├── trends.py             # Trending data fetching (multi-threaded)
│   └── alert_manager.py     # Alert management module
├── agent_set/                # Agent components
│   ├── agent_set.py          # Agent creation
│   ├── tools_set.py          # Tool set definitions
│   └── skill_set.py         # Skill configuration
├── model_set/                # Model configuration
│   └── model_set.py          # DeepSeek model configuration
├── static/                   # Frontend static resources
│   ├── index.html            # Main page
│   ├── style.css             # Stylesheet
│   ├── config.js             # Configuration and constants
│   ├── state.js              # State management
│   ├── dom.js                # DOM element cache
│   ├── utils.js              # Utility functions
│   ├── chat.js               # Chat functionality
│   ├── history.js            # History records
│   ├── todo.js              # Todo items
│   ├── skills.js            # Skills/tools
│   ├── trends.js            # Trending news
│   ├── alerts.js            # Alert functionality
│   ├── links.js             # Association search
│   ├── init.js              # Initialization and event binding
│   ├── alert.html           # Alert detail page
│   ├── alert.js             # Alert detail page logic
│   └── alert.css             # Alert detail page styles
├── data/                     # Data storage directory
│   ├── alerts.json           # Alert rules storage
│   └── alert_history.json    # Alert history records
├── prompt/                   # Prompt configuration
│   └── AGENTS.md             # Agent system prompts
├── chat_history/             # Conversation history storage
├── pyproject.toml            # Project configuration
└── README.md                 # Project documentation
```

## Features

### 1. Smart Conversation

- Continuous conversation with context memory
- Automatic task decomposition and execution
- SSE streaming responses

### 2. TODO Task Management

- **Auto-creation**: Automatically generates task list when user input >= 20 characters
- **Smart Updates**: AI automatically analyzes task completion status
- **Manual Skip**: Short inputs are answered directly without creating TODO

### 3. Tool Calling

The system includes multiple built-in tools:

| Tool Name | Description |
|-----------|-------------|
| run_powershell | Execute PowerShell commands |
| write_file | Write file content |
| read_text_file | Read text file content |
| read_binary_file | Read binary file content |
| fetch_rss_feed | Fetch and parse RSS/Atom feeds |
| web_search | Search the web using DuckDuckGo |

### 4. Intelligence Panel

- **INTELLIGENCE Panel**: Display trending searches (data source: [orz.ai](https://orz.ai/))
  - HOT: Aggregated trending from multiple platforms (Baidu, Weibo, Zhihu, Douyin, Bilibili, etc.)
  - ALERTS: Keyword monitoring and alerts
  - LINKS: Keyword association analysis
  - RSS: Custom RSS subscription
- All items are clickable and link to original pages

### 5. Keyword Monitoring & Alerts

- **Add Monitoring**: Enter keywords in ALERTS tab to add monitoring
- **Auto-detection**: Checks trending data every second, alerts immediately on match
- **Real-time Push**: SSE pushes new alerts to frontend instantly
- **Event Timeline**: Click keyword to view complete alert history
- **Persistent Storage**: Alert rules and history stored in `data/` directory
- **Duplicate Detection**: Same keyword (case-insensitive) cannot be added, shows "already exists"

### 6. Keyword Association Analysis

- **Association Search**: Enter keywords in LINKS tab to analyze associations
- **Smart Analysis**: Analyzes related keywords from current trending data
- **One-click Alert**: Click any association keyword to add to ALERTS
- **Relevance Score**: Shows relevance percentage for each associated keyword

### 7. RSS Subscription

- **Add Subscription**: Enter RSS/Atom URL in RSS tab to add
- **Duplicate Detection**: Same URL (case-insensitive) cannot be added, shows "URL already exists"

### 7. Frontend Features

- **Real-time Progress**: Tool calling and task status update in real-time
- **Responsive Design**: Adapts to different screen sizes
- **Left Sidebar**: Displays HISTORY + TODO + CAPABILITIES
- **Right Sidebar**: INTELLIGENCE panel (50% width)
- **Chat Area**: 33% width

## Quick Start

### Requirements

- Python 3.11 or higher
- DeepSeek API Key

### Installation

1. Clone the project:

```bash
git clone https://github.com/CuteCuteYu/onekiil4all.git
cd onekiil4all
```

2. Install dependencies:

```bash
uv sync
```

3. Configure environment variables:

Add `DEEPSEEK_API_KEY` to system environment variables with your DeepSeek API Key value.

Or create a `.env` file:

```bash
DEEPSEEK_API_KEY=your_api_key_here
```

4. Start the service:

```bash
uv run python -m web.web_server
```

5. Access the interface:

Open browser and visit `http://localhost:8000`

## Usage Guide

### Basic Conversation

1. Enter your question in the input box
2. Click SEND or press Enter to send
3. AI will automatically answer your question

### Creating Tasks

When input exceeds 20 characters, the system will automatically:

1. Analyze user requirements
2. Generate task list (TODO)
3. Execute steps sequentially
4. Display execution progress in real-time

### Tool Calling

The system automatically determines if tool calling is needed:

- Read/Write files: Use file-related tools
- Execute commands: Use run_powershell

All tool calls display real-time progress on the frontend.

## Configuration

### Model Configuration

Modify `model_set/model_set.py` to change the model:

```python
model = ChatOpenAI(
    model="deepseek-chat",           # Model name
    api_key=convert_to_secret_str(api_key),
    base_url="https://api.deepseek.com",  # API URL
)
```

### Tool Configuration

Modify `agent_set/tools_set.py` to add or modify tools.

### Task Threshold

Modify `message_length >= 20` in `web/web_server.py` to adjust TODO creation threshold.

## API Endpoints

The service provides the following REST APIs:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Returns frontend page |
| `/alert` | GET | Alert detail page |
| `/static/*` | GET | Static resources |
| `/api/chat` | POST | Send chat message (SSE streaming) |
| `/api/new` | POST | Create new conversation |
| `/api/history` | GET | Get conversation history |
| `/api/history/{tid}` | GET | Get specific conversation |
| `/api/history/{tid}` | DELETE | Delete conversation |
| `/api/todo` | GET | Get TODO list |
| `/api/skills` | GET | Get available skills |
| `/api/tools` | GET | Get available tools |
| `/api/trends` | GET | Get trending and intelligence info |
| `/api/alerts` | GET/POST | Get/create alert rules |
| `/api/alerts/{id}` | DELETE | Delete alert rule |
| `/api/alerts/{id}/toggle` | POST | Toggle alert status |
| `/api/alerts/history` | GET | Get alert history |
| `/api/alerts/history/all` | DELETE | Clear alert history |
| `/api/alerts/timeline/{keyword}` | GET | Get keyword timeline |
| `/api/alerts/stream` | GET | SSE alert stream (real-time push) |
| `/api/rss` | GET/POST | Get/create RSS subscription |
| `/api/rss/{id}` | DELETE | Delete RSS source |
| `/api/rss/{id}/toggle` | POST | Enable/disable RSS source |
| `/api/rss/articles` | GET | Get all RSS sources latest articles |
| `/api/rss/stream` | GET | SSE RSS article stream (real-time push) |

## RSS Subscription Feature

### Description

- **Add Subscription**: In INTELLIGENCE panel's RSS tab, enter RSS/Atom URL to add
- **Scheduled Fetch**: Background thread fetches every 60 seconds (check interval 1 second)
- **Real-time Push**: New articles pushed to frontend via SSE
- **Article Storage**: Each source keeps latest 10 articles

### Usage Example

Add RSS subscription:
```bash
curl -X POST http://localhost:8000/api/rss \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.ruanyifeng.com/blog/atom.xml"}'
```

### Graceful Shutdown

**Important**: Close browser tab first to disconnect SSE connections before pressing Ctrl+C.

Exit steps:
1. Close browser tab (or refresh to disconnect SSE connections)
2. Press Ctrl+C to exit

## Performance Optimization

### Multi-threading Concurrency

- **Trending Data Fetching**: Uses `ThreadPoolExecutor` to fetch data from multiple platforms concurrently, reducing time from ~165 seconds (sequential) to ~2 seconds
- **Background Alert Checking**: Uses `asyncio.to_thread()` to avoid blocking main event loop, ensuring smooth UI responsiveness
- **Graceful Shutdown**: Properly closes background tasks and thread pool on service stop, preventing Ctrl+C hang

### Technical Details

```python
# trends.py - concurrent fetching
_executor = ThreadPoolExecutor(max_workers=8)
futures = {_executor.submit(_fetch_platform, p): p for p in platforms}
```

```python
# web_server.py - async execution
trends = await asyncio.to_thread(get_trends, check_alerts=True)
```

```python
# web_server.py - graceful shutdown
alert_checker_task.cancel()
await asyncio.wait_for(alert_checker_task, timeout=2.0)
_executor.shutdown(wait=False)
```

## FAQ

### Q: How to get API Key?

A: Visit [DeepSeek Open Platform](https://platform.deepseek.com/) to register and get API Key.

### Q: Why do tool calls fail?

A: Check if PowerShell is available and if commands have permission to execute.

### Q: How to modify the model?

A: Modify the model configuration in `model_set/model_set.py`, supports OpenAI-compatible APIs.

### Q: How to adjust sidebar width?

A: Move mouse to sidebar edge, when double-arrow cursor appears, drag to resize.

## Contributing

Feel free to submit Issues and Pull Requests!

## License

MIT License

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [DeepSeek](https://www.deepseek.com/) - Large language model
- [DeepAgents](https://github.com/deepagents) - Agent framework
- [orz.ai](https://orz.ai/) - Trending data API provider
