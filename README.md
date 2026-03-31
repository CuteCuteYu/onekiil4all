# 上古必斩必杀

AI 智能助手 - 基于 LangChain + DeepSeek 构建

## 项目简介

上古必斩必杀 是一个功能强大的 AI 助手，支持：

- **智能对话**：基于 DeepSeek 大语言模型
- **任务管理**：自动生成和管理 TODO 列表
- **工具调用**：支持多种工具（文件操作、命令执行等）
- **Web 界面**：现代化的响应式前端界面

## 技术栈

- **后端**：Python 3.11+, FastAPI, **LangChain**, LangGraph
- **AI 模型**：DeepSeek Chat API
- **前端**：原生 HTML/CSS/JavaScript
- **架构**：Agent 架构，支持工具调用和自动迭代
- **参考框架**：LangChain、DeepAgents

## 项目结构

```
onekiil4all/
├── web/                      # Web 服务端代码
│   ├── web_server.py         # FastAPI Web 服务器
│   ├── chat_handler.py       # 聊天处理器
│   ├── conversation.py       # 对话管理
│   ├── task_analyzer.py      # 任务分析器
│   ├── todo_manager.py       # TODO 管理器
│   ├── trends.py             # 热搜数据获取（多线程并发）
│   └── alert_manager.py      # 告警管理模块
├── agent_set/                # Agent 组件
│   ├── agent_set.py          # Agent 创建
│   ├── tools_set.py          # 工具集定义
│   └── skill_set.py          # 技能配置
├── model_set/                # 模型配置
│   └── model_set.py          # DeepSeek 模型配置
├── static/                   # 前端静态资源
│   ├── index.html            # 主页面
│   ├── app.js                # 前端逻辑
│   ├── style.css             # 样式文件
│   ├── alert.html            # 告警详情页
│   ├── alert.js              # 告警详情页逻辑
│   └── alert.css             # 告警详情页样式
├── data/                     # 数据存储目录
│   ├── alerts.json           # 告警规则存储
│   └── alert_history.json    # 告警历史记录
├── prompt/                   # 提示词配置
│   └── AGENTS.md             # Agent 系统提示
├── chat_history/             # 对话历史存储
├── pyproject.toml            # 项目配置
└── README.md                 # 项目文档
```

## 功能特性

### 1. 智能对话

- 支持连续对话和上下文记忆
- 自动任务分解和执行
- SSE 流式响应

### 2. TODO 任务管理

- **自动创建**：用户输入 >= 20 个字符时自动生成任务清单
- **智能更新**：AI 自动分析任务完成状态
- **手动跳过**：简短输入直接回答，不创建 TODO

### 3. 工具调用

系统内置多种工具：

| 工具名称 | 功能描述 |
|---------|---------|
| run_powershell | 执行 PowerShell 命令 |
| write_file | 写入文件内容 |
| read_text_file | 读取文本文件内容 |
| read_binary_file | 读取二进制文件内容 |
| fetch_rss_feed | 获取并解析 RSS/Atom 订阅源 |
| web_search | 使用 DuckDuckGo 搜索网络 |

### 4. 情报分析面板

- **INTELLIGENCE 面板**：展示热门搜索和科技资讯（数据来源：[orz.ai](https://orz.ai/)）
  - HOT：聚合多个平台的热门热搜（百度、微博、知乎、抖音、B站等）
  - GITHUB：GitHub Trending 项目
  - TECH：科技新闻（少数派、36氪、掘金、V2EX、Hacker News）
  - ALERTS：关键词监控和告警
- 所有条目可点击跳转原始页面

### 5. 关键词监控与告警

- **添加监控**：在 ALERTS 标签页输入关键词添加监控
- **自动检测**：每秒自动检查热点数据，发现匹配关键词立即告警
- **实时推送**：通过 SSE 实时推送新告警到前端
- **事件时间线**：点击关键词查看完整的告警事件历史
- **持久化存储**：告警规则和历史记录保存在 `data/` 目录

### 6. 前端界面特性

- **实时进度显示**：工具调用、任务状态实时更新
- **响应式设计**：适配不同屏幕尺寸
- **左侧边栏**：显示 HISTORY + TODO + CAPABILITIES
- **右侧边栏**：INTELLIGENCE 情报面板（占据 50% 宽度）
- **聊天区域**：占据 33% 宽度

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- DeepSeek API Key

### 安装步骤

1. 克隆项目：

```bash
git clone https://github.com/CuteCuteYu/onekiil4all.git
cd onekiil4all
```

2. 安装依赖：

```bash
uv sync
```

3. 配置环境变量：

在系统环境变量中添加 `DEEPSEEK_API_KEY`，值为你的 DeepSeek API Key。

或者创建 `.env` 文件：

```bash
DEEPSEEK_API_KEY=your_api_key_here
```

4. 启动服务：

```bash
uv run python -m web.web_server
```

5. 访问界面：

打开浏览器访问 `http://localhost:8000`

## 使用指南

### 基本对话

1. 在输入框中输入问题
2. 点击 SEND 或按 Enter 发送
3. AI 将自动回答问题

### 创建任务

当输入内容超过 20 个字符时，系统会自动：

1. 分析用户需求
2. 生成任务清单（TODO）
3. 按步骤依次执行
4. 实时显示执行进度

### 工具调用

系统会自动判断是否需要调用工具：

- 读写文件：调用 file 相关工具
- 执行命令：调用 run_powershell

所有工具调用都会在前端实时显示进度。

## 配置说明

### 模型配置

修改 `model_set/model_set.py` 可以更换模型：

```python
model = ChatOpenAI(
    model="deepseek-chat",           # 模型名称
    api_key=convert_to_secret_str(api_key),
    base_url="https://api.deepseek.com",  # API 地址
)
```

### 工具配置

修改 `agent_set/tools_set.py` 可以添加或修改工具。

### 任务阈值

修改 `web/web_server.py` 中的 `message_length >= 20` 可以调整 TODO 创建阈值。

## API 接口

服务提供以下 REST API：

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/` | GET | 返回前端页面 |
| `/alert` | GET | 告警详情页面 |
| `/static/*` | GET | 静态资源 |
| `/api/chat` | POST | 发送聊天消息（SSE 流式） |
| `/api/new` | POST | 创建新对话 |
| `/api/history` | GET | 获取对话历史 |
| `/api/history/{tid}` | GET | 获取指定对话 |
| `/api/history/{tid}` | DELETE | 删除对话 |
| `/api/todo` | GET | 获取 TODO 列表 |
| `/api/skills` | GET | 获取可用技能 |
| `/api/tools` | GET | 获取可用工具 |
| `/api/trends` | GET | 获取热门搜索和情报信息 |
| `/api/alerts` | GET/POST | 获取/创建告警规则 |
| `/api/alerts/{id}` | DELETE | 删除告警规则 |
| `/api/alerts/{id}/toggle` | POST | 切换告警状态 |
| `/api/alerts/history` | GET | 获取告警历史 |
| `/api/alerts/history/all` | DELETE | 清空告警历史 |
| `/api/alerts/timeline/{keyword}` | GET | 获取关键词时间线 |
| `/api/alerts/stream` | GET | SSE 告警流（实时推送） |

## 性能优化

### 多线程并发

- **热点数据获取**：使用 `ThreadPoolExecutor` 并发获取多个平台数据，原来串行获取需要约 165 秒，优化后仅需约 2 秒
- **后台告警检查**：使用 `asyncio.to_thread()` 避免阻塞主事件循环，确保 UI 响应流畅

### 技术细节

```python
# trends.py - 并发获取
_executor = ThreadPoolExecutor(max_workers=8)
futures = {_executor.submit(_fetch_platform, p): p for p in platforms}
```

```python
# web_server.py - 异步执行
trends = await asyncio.to_thread(get_trends, check_alerts=True)
```

## 常见问题

### Q: API Key 如何获取？

A: 访问 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册并获取 API Key。

### Q: 为什么工具调用失败？

A: 检查 PowerShell 是否可用，以及命令是否有权限执行。

### Q: 如何修改模型？

A: 修改 `model_set/model_set.py` 中的模型配置，支持 OpenAI 兼容的 API。

### Q: 前端侧边栏如何调整宽度？

A: 将鼠标移动到侧边栏边缘，出现双箭头光标后拖动即可。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [DeepSeek](https://www.deepseek.com/) - 大语言模型
- [DeepAgents](https://github.com/deepagents) - Agent 框架
- [orz.ai](https://orz.ai/) - 热点数据 API 提供
