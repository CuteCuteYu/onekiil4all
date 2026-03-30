# Onekiil4all

AI Intelligent Assistant - Built with LangChain + DeepSeek

## Project Overview

Onekiil4all is a powerful AI assistant that supports:

- **Smart Conversation**: Based on DeepSeek large language model
- **Task Management**: Auto-generate and manage TODO lists
- **Tool Calling**: Support for multiple tools (file operations, command execution, etc.)
- **Web Interface**: Modern responsive frontend

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, LangChain, LangGraph
- **AI Model**: DeepSeek Chat API
- **Frontend**: Native HTML/CSS/JavaScript
- **Architecture**: Agent architecture with tool calling and auto-iteration

## Project Structure

```
onekiil4all/
├── web/                      # Web server code
│   ├── web_server.py         # FastAPI web server
│   ├── chat_handler.py       # Chat handler
│   ├── conversation.py       # Conversation management
│   ├── task_analyzer.py      # Task analyzer
│   ├── todo_manager.py       # TODO manager
│   └── trends.py             # Trending data fetching
├── agent_set/                # Agent components
│   ├── agent_set.py          # Agent creation
│   ├── tools_set.py          # Tool set definitions
│   └── skill_set.py         # Skill configuration
├── model_set/                # Model configuration
│   └── model_set.py          # DeepSeek model configuration
├── static/                   # Frontend static resources
│   ├── index.html            # Main page
│   ├── app.js                # Frontend logic
│   └── style.css             # Stylesheet
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

- **INTELLIGENCE Panel**: Display trending searches and tech news
  - HOT: Aggregated trending from multiple platforms (Baidu, Weibo, Zhihu, Douyin, Bilibili, etc.)
  - GITHUB: GitHub Trending projects
  - TECH: Tech news (少数派, 36Kr, 掘金, V2EX, Hacker News)
- All items are clickable and link to original pages

### 5. Frontend Features

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
