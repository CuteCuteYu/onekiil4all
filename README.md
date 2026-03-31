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
│   ├── style.css             # 样式文件
│   ├── config.js             # 配置和常量
│   ├── state.js              # 状态管理
│   ├── dom.js                # DOM元素缓存
│   ├── utils.js              # 辅助函数
│   ├── chat.js               # 聊天功能
│   ├── history.js            # 历史记录
│   ├── todo.js              # 待办事项
│   ├── skills.js            # 技能/工具
│   ├── init.js              # 初始化和事件绑定
│   ├── alert.html           # 告警详情页
│   ├── alert.js             # 告警详情页逻辑
│   ├── alert.css            # 告警详情页样式
│   └── intelligence/        # 情报模块
│       ├── trends.js        # 热点资讯
│       ├── alerts.js        # 告警功能
│       ├── links.js         # 关联搜索
│       └── rss.js           # RSS订阅
├── web/                      # FastAPI Web服务器
│   ├── web_server.py         # 主入口
│   ├── chat_handler.py       # 聊天处理
│   ├── conversation.py      # 会话管理
│   ├── task_analyzer.py     # 任务分析
│   ├── todo_manager.py      # TODO管理
│   └── intelligence/         # 情报模块
│       ├── trends.py         # 热点数据获取
│       ├── alert_manager.py  # 告警管理
│       └── rss_manager.py    # RSS订阅管理
├── data/                     # 数据存储目录
│   ├── alerts.json           # 告警规则存储
│   ├── alert_history.json    # 告警历史记录
│   └── rss_sources.json      # RSS订阅源存储
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

- **INTELLIGENCE 面板**：展示热门搜索（数据来源：[orz.ai](https://orz.ai/)）
  - HOT：聚合多个平台的热门热搜（百度、微博、知乎、抖音、B站等）
  - ALERTS：关键词监控和告警
  - LINKS：关键词关联分析
  - RSS：自定义 RSS 订阅源
- 所有条目可点击跳转原始页面

### 5. 关键词监控与告警

- **添加监控**：在 ALERTS 标签页输入关键词添加监控
- **自动检测**：每秒自动检查热点数据，发现匹配关键词立即告警
- **实时推送**：通过 SSE 实时推送新告警到前端
- **事件时间线**：点击关键词查看完整的告警事件历史
- **持久化存储**：告警规则和历史记录保存在 `data/` 目录
- **重复检测**：相同关键词（忽略大小写）无法重复添加，会提示"已存在"

### 6. 关键词关联分析

- **关联搜索**：在 LINKS 标签页输入关键词进行关联分析
- **智能关联**：分析当前热点数据中与输入关键词相关的其他词汇
- **一键告警**：点击任意关联词条自动添加到 ALERTS 监控
- **关联度显示**：显示关联词条的相关性百分比

### 7. RSS 订阅

- **添加订阅**：在 RSS 标签页输入 RSS/Atom 地址添加
- **重复检测**：相同 URL（忽略大小写）无法重复添加，会提示"URL 已存在"

### 8. 安全情报

- **IP归属地查询**：查询IP归属地、运营商（跳转站长工具）
- **WHOIS查询**：查询域名注册信息（跳转站长工具）
- **CVE漏洞查询**：查询CVE漏洞详情（阿里云漏洞库）
- **网站安全检测**：检测网站安全状况（跳转站长工具）

### 9. 前端界面特性

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
| `/api/rss` | GET/POST | 获取/添加 RSS 订阅源 |
| `/api/rss/{id}` | DELETE | 删除 RSS 源 |
| `/api/rss/{id}/toggle` | POST | 启用/禁用 RSS 源 |
| `/api/rss/articles` | GET | 获取所有 RSS 源最新文章 |
| `/api/rss/stream` | GET | SSE RSS 文章流（实时推送） |

## RSS 订阅功能

### 功能说明

- **添加订阅源**：在 INTELLIGENCE 面板的 RSS 标签页，输入 RSS/Atom 订阅地址添加
- **定时抓取**：后台线程每 60 秒自动抓取一次（每 1 秒检查间隔）
- **实时推送**：新文章通过 SSE 实时推送到前端
- **文章存储**：每个源保留最近 10 条文章

### 使用示例

添加 RSS 订阅：
```bash
curl -X POST http://localhost:8000/api/rss \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.ruanyifeng.com/blog/atom.xml"}'
```

### 优雅关闭

**重要**：退出服务前请先关闭浏览器标签页，断开 SSE 连接后再按 Ctrl+C。

退出步骤：
1. 关闭浏览器标签页（或刷新页面断开 SSE 连接）
2. 按 Ctrl+C 退出服务

## 性能优化

### 多线程并发

- **热点数据获取**：使用 `ThreadPoolExecutor` 并发获取多个平台数据，原来串行获取需要约 165 秒，优化后仅需约 2 秒
- **后台告警检查**：使用 `asyncio.to_thread()` 避免阻塞主事件循环，确保 UI 响应流畅
- **优雅关闭**：服务停止时正确关闭后台任务和线程池，避免 Ctrl+C 卡住

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

```python
# web_server.py - 优雅关闭
alert_checker_task.cancel()
await asyncio.wait_for(alert_checker_task, timeout=2.0)
_executor.shutdown(wait=False)
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
- [站长工具](https://www.chinaz.com/) - IP查询、WHOIS、网站安全检测
- [阿里云漏洞库](https://avd.aliyun.com/) - CVE漏洞查询
