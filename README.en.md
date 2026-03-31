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
│   ├── app.js                # Frontend logic
│   ├── style.css             # Stylesheet
│   ├── alert.html            # Alert detail page
│   ├── alert.js              # Alert detail page logic
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

- **INTELLIGENCE Panel**: Display trending searches and tech news (data source: [orz.ai](https://orz.ai/))
  - HOT: Aggregated trending from multiple platforms (Baidu, Weibo, Zhihu, Douyin, Bilibili, etc.)
  - GITHUB: GitHub Trending projects
  - TECH: Tech news (少数派, 36Kr, 掘金, V2EX, Hacker News)
  - ALERTS: Keyword monitoring and alerts
  - LINKS: Keyword association analysis
- All items are clickable and link to original pages

### 5. Keyword Monitoring & Alerts

- **Add Monitoring**: Enter keywords in ALERTS tab to add monitoring
- **Auto-detection**: Checks trending data every second, alerts immediately on match
- **Real-time Push**: SSE pushes new alerts to frontend instantly
- **Event Timeline**: Click keyword to view complete alert history
- **Persistent Storage**: Alert rules and history stored in `data/` directory

### 6. Keyword Association Analysis

- **Association Search**: Enter keywords in LINKS tab to analyze associations
- **Smart Analysis**: Analyzes related keywords from current trending data
- **One-click Alert**: Click any association keyword to add to ALERTS
- **Relevance Score**: Shows relevance percentage for each associated keyword

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
