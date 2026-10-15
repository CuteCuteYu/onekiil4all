# 上古必斩必杀

AI 智能助手 - 基于 LangChain + Anthropic 兼容模型构建

## 项目简介

上古必斩必杀 是一个功能强大的 AI 助手，支持：

- **智能对话**：Anthropic 协议兼容的大语言模型（Claude / GLM 等）
- **任务管理**：自动生成和管理 TODO 列表
- **工具调用**：支持多种工具（文件操作、命令执行、图谱查询等）
- **情报画板**：本地知识图谱可视化 + GraphRAG 数据准备（多画板管理、实体关系编辑、一键导出索引）
- **GraphRAG 对话**：画板保存后 Agent 自动接入图谱检索工具，可直接问答画板中的实体关系
- **Web 界面**：现代化的响应式前端界面

## 技术栈

- **后端**：Python 3.11+, FastAPI, **LangChain**, LangGraph
- **AI 模型**：Anthropic 兼容 API（默认读取 `ANTHROPIC_*` 环境变量）
- **中文分词**：jieba（关联分析中文关键词提取）
- **前端**：原生 HTML/CSS/JavaScript
- **架构**：Agent 架构，支持工具调用和自动迭代
- **参考框架**：LangChain、DeepAgents

## 项目结构

```
onekiil4all/
├── web/                      # Web 服务端代码
│   ├── web_server.py         # FastAPI 应用装配入口（生命周期/静态资源/路由注册）
│   ├── background_tasks.py   # 后台任务（告警检查/RSS抓取循环）
│   ├── chat_handler.py       # 聊天处理器（含 token 级流式输出）
│   ├── message_utils.py      # 消息转换工具（content/流式文本/JSONL转LangChain）
│   ├── conversation.py       # 对话管理
│   ├── task_analyzer.py      # 任务分析器（检查任务完成状态）
│   ├── task_cache.py         # 任务状态缓存
│   ├── task_prompts.py       # 任务分析提示词构建
│   ├── todo_manager.py       # TODO 管理器
│   ├── todo_prompts.py       # TODO 提示词构建
│   ├── sessions.py           # 会话管理（带上限淘汰）
│   ├── chat_history_store.py # 对话历史存储（JSONL 追加写入）
│   ├── sse.py                # SSE 事件广播（按连接 fan-out）
│   ├── paths.py              # 项目路径常量（锚定根目录）
│   ├── api/                  # API 路由（按职责拆分）
│   │   ├── chat_api.py       # 聊天 SSE 流式接口
│   │   ├── session_api.py    # 会话列表/TODO 查询
│   │   ├── history_api.py    # 对话历史 CRUD
│   │   ├── meta_api.py       # 技能/工具路由
│   │   ├── intelligence_api.py # 热点资讯/关联分析
│   │   ├── alert_api.py      # 告警规则/历史/SSE
│   │   ├── rss_api.py        # RSS 订阅/文章/SSE
│   │   └── canvas_api.py     # 情报画板/图谱/类型/GraphRAG 路由
│   └── intelligence/         # 情报模块
│       ├── trends/           # 热点数据包（按职责拆分）
│       │   ├── __init__.py   # 主入口（get_trends + 缓存）
│       │   ├── parsers.py    # 各平台解析纯函数
│       │   ├── fetchers.py   # 网络抓取与并发调度
│       │   ├── keywords.py   # 中英文关键词提取
│       │   └── associations.py # 关键词关联分析
│       ├── graph_board.py    # 画板管理/图谱 CRUD/已保存检查/GraphRAG 检索
│       ├── alert_manager.py  # 告警管理
│       ├── alert_models.py   # 告警数据模型
│       ├── rss_manager.py    # RSS 订阅管理
│       └── rss_parser.py     # RSS/Atom 公共解析
├── agent_set/                # Agent 组件
│   ├── agent_set.py          # Agent 创建（FilesystemBackend + 技能/记忆/MCP 装配）
│   ├── mcp_set.py            # MCP 配置加载与工具挂载（读项目内 mcp/mcp.json）
│   ├── tools/                # 工具集包（按职责拆分）
│   │   ├── __init__.py       # 工具列表导出
│   │   ├── shell.py          # PowerShell 命令执行
│   │   ├── files.py          # 文件读写（相对路径锚定项目根）
│   │   ├── search.py         # 网络搜索与 RSS 获取
│   │   ├── graphrag.py       # 画板状态检查 + GraphRAG 检索工具
│   │   └── todo.py           # 任务清单读取/更新工具
│   └── skill_set.py          # 技能加载（读项目内 skills/）
├── model_set/                # 模型配置
│   └── model_set.py          # 模型配置（读 ANTHROPIC_* 环境变量，缺凭据启动即报错）
├── static/                   # 前端静态资源
│   ├── index.html            # 主页面
│   ├── style.css             # 样式文件
│   ├── canvas.css            # 情报画板样式（与主应用风格统一）
│   ├── config.js             # 配置和常量
│   ├── state.js              # 全局状态
│   ├── dom.js                # DOM元素缓存
│   ├── utils.js              # 辅助函数
│   ├── chat.js               # 聊天功能
│   ├── history.js            # 历史记录
│   ├── todo.js               # 待办事项
│   ├── skills.js             # 技能/工具
│   ├── canvas.js             # 情报画板（Cytoscape 图谱可视化 + 状态刷新）
│   ├── init.js               # 初始化和事件绑定
│   ├── alert.html            # 告警详情页
│   ├── alert.js              # 告警详情页逻辑
│   ├── alert.css             # 告警详情页样式
│   └── intelligence/         # 情报模块
│       ├── trends.js         # 热点资讯
│       ├── alerts.js         # 告警功能
│       ├── links.js          # 关联搜索
│       ├── rss.js            # RSS订阅
│       └── profile.js       # 消息心理画像
├── data/                     # 数据存储目录（运行时生成，不入库）
│   ├── alerts.json           # 告警规则存储
│   ├── alert_history.json    # 告警历史记录
│   ├── rss_sources.json      # RSS订阅源存储
│   ├── graph_data.json       # 旧版画板单文件（迁移源）
│   └── graphs/               # 画板目录（每个画板一个 JSON）
├── tests/                    # pytest 测试
├── prompt/                   # 提示词配置
│   └── AGENTS.md             # Agent 系统提示（memory，直接从磁盘读取）
├── skills/                   # 项目内技能目录（每个技能一个文件夹 + SKILL.md）
│   ├── osint-recon/          # 内置：OSINT 情报搜集流程（提到“搜集/搜索/调查”等触发）
│   └── se-psych-profile/     # 内置：社会工程学消息心理画像（杠杆/阶段/原型分析框架）
│   └── se-psych-profile/     # 内置：社会工程学消息心理画像（心理杠杆/话术阶段/角色原型）
├── mcp/                      # 项目内 MCP 配置（不读 Claude Code/Desktop 全局配置）
│   ├── mcp.json              # MCP 服务器列表（web / ddg，已实测可用）
│   └── README.md             # 配置格式 + 国内网络注意事项 + 实测清单
├── chat_history/             # 对话历史存储（JSONL，运行时生成，不入库）
├── start.bat / stop.bat      # Windows 启动 / 停止脚本
├── start.sh / stop.sh        # Linux / macOS 启动 / 停止脚本
├── pyproject.toml            # 项目配置
└── README.md                 # 项目文档
```

## 功能特性

### 1. 智能对话

- 支持连续对话和上下文记忆（历史从 JSONL 持久化恢复，服务重启不丢失）
- 自动任务分解和执行
- SSE 流式响应
- **运行中可中断**：Agent 处理时显示 STOP 按钮，点击立即中断；中断时已生成的部分回复自动保存到历史（标记 `interrupted`），TODO 保留（任务未完成）

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
| graphrag_status | 检查当前情报画板接入状态（画板名/是否已保存/节点关系数） |
| graphrag_query | GraphRAG 检索当前画板实体（名称/类型/描述/属性/来源），返回实体详情与关联关系 |
| graph_add_node | 向当前画板写入/更新实体节点（SE 分析沉淀；画板打开即可写，支持批量） |
| graph_add_edge | 向当前画板写入/更新关系边（USES/STAGE/PERSONA 等大写关系） |

> 说明：`graphrag_query` 仅在当前画板处于「已保存」状态时可用；未保存时返回引导提示。画板切换后 Agent 查询自动跟随当前画板。`graph_add_node` / `graph_add_edge` 只要画板已打开即可写入（写入会使画板变为未保存，属正常现象，可继续批量写入，完成后由用户在 CANVAS 一键保存）；**Agent 写入前必须获得用户同意**。

### 4. 情报分析面板

- **INTELLIGENCE 面板**：展示热门搜索（自建多平台抓取，直连各平台官方接口，不依赖第三方聚合站）
  - HOT：聚合多个平台的热搜排行榜（微博、百度、头条、B站、抖音）与 GitHub 新仓库、科技新闻（HackerNews、少数派、钛媒体、36氪、InfoQ）
  - ALERTS：关键词监控和告警
  - LINKS：关键词关联分析
  - RSS：自定义 RSS 订阅源
  - PROFILE：消息心理画像（见第 8 节）
  - PROFILE：消息心理画像（见下节）
- 所有条目可点击跳转原始页面

### 5. 关键词监控与告警

- **添加监控**：在 ALERTS 标签页输入关键词添加监控
- **自动检测**：后台每 30 秒自动检查热点数据（数据有 30 秒缓存，不会重复抓取），发现匹配关键词立即告警
- **实时推送**：通过 SSE 实时推送新告警到前端（多标签页各自收到完整事件流，事件单层转发，前端可直接读取字段）
- **新告警提醒**：收到新告警时 ALERTS 标签显示未读数字徽标，规则项与历史项脉冲高亮，切到标签页即清除
- **规则统计**：每条规则直接显示触发次数与最近触发时间（由 `/api/alerts` 附带返回，无需二次请求）
- **本地即时渲染**：新告警先本地插入历史列表并更新计数，5 秒后与后端对齐一次，避免每次告警全量重拉
- **断线补偿**：SSE 断线重连成功后自动补拉规则与历史，不遗漏断线期间的告警
- **多标签同步**：任一标签页增删改规则后广播 `alert_updated`，其他标签页自动同步
- **事件时间线**：点击关键词查看完整的告警事件历史
- **持久化存储**：告警规则和历史记录保存在 `data/` 目录
- **重复检测**：相同关键词（忽略大小写）无法重复添加，会提示"已存在"

### 6. 关键词关联分析

- **关联搜索**：在 LINKS 标签页输入关键词（中英文均可）进行关联分析
- **全网搜索 + AI 总结**：通过搜索引擎（DuckDuckGo / Bing）抓取相关网页标题，交由项目 AI 模型总结出 5~12 个高相关关键词（品牌/产品/实体名，中英文混合）
- **两级智能回退**：
  1. AI 模型调用失败（如内容审核拦截、限流）时，直接从已抓取的搜索标题中提取关键词（jieba 中文分词 + 英文实词），保证人名/地名等敏感词也能返回关联结果
  2. 搜索也失败时，回退到内置热点数据分析（中英文关键词均可提取），保证功能不中断
- **中文关键词支持**：使用 jieba 分词提取中文关联词，过滤中文停用词，中文关键词不再返回空结果
- **结果缓存**：同一关键词 60 秒内重复搜索直接返回缓存结果
- **一键告警**：点击任意关联词条自动添加到 ALERTS 监控（重复词提示"已存在"，成功后高亮新规则）
- **关联度显示**：显示关联词条的相关性百分比（按 AI 输出的相关度排序递减）

### 7. RSS 订阅

- **添加订阅**：在 RSS 标签页输入 RSS/Atom 订阅地址添加
- **格式支持**：支持 RSS 2.0、RSS 1.0（RDF/XML）和 Atom 三种 XML 格式
- **立即显示**：添加订阅源后立即抓取文章并显示，无需手动刷新（后台仍会按周期自动更新）
- **重复检测**：相同 URL（忽略大小写）无法重复添加，会提示"URL 已存在"

### 8. 消息心理画像（PROFILE / 社工程学防御分析）

在 INTELLIGENCE 面板的 **PROFILE** 标签页，粘贴可疑消息样本（聊天记录/短信/邮件/客服对话），一键生成**纯防御导向**的心理画像报告：

- **七段式报告**：①话术阶段判定 ②冒充角色原型 ③心理杠杆命中表（权威/紧迫/恐惧/贪婪/社会认同/互惠/孤立/羞耻等，附原文引用与强度） ④逐句标注操纵手法与破绽 ⑤群体易感性评估（哪类人群高危，不指向具体个人） ⑥识别与应对要点（如 96110、24h冷静期） ⑦置信度与局限
- **分析框架内置**：`skills/se-psych-profile/` 技能提供心理杠杆清单、五阶段话术模型、角色原型库，Agent 自动按框架执行
- **红线约束**：只分析不生成——拒绝编写/优化任何操纵话术，不为真实个人建立心理档案，群体维度评估不指向具体个人
- **沉淀到 CANVAS**：报告完成后一键把骗术模式/心理杠杆/话术阶段/冒充原型写入情报画板（Agent 征得同意后调用 `graph_add_node` / `graph_add_edge`，以 FraudPattern 为中心连接 USES/STAGE/PERSONA 关系）
- **失败可见**：模型调用失败时面板明确提示失败，不再显示空白成功卡片（聊天区同步显示红色错误）

### 9. 前端界面特性

- **实时进度显示**：工具调用、任务状态实时更新
- **响应式设计**：适配不同屏幕尺寸
- **左侧边栏**：显示 HISTORY + TODO + CAPABILITIES
- **右侧边栏**：INTELLIGENCE 情报面板（占据 50% 宽度）
- **聊天区域**：占据 33% 宽度

### 10. 情报画板（CANVAS / GraphRAG）

集成自 GraphRAG Viz，在 INTELLIGENCE 面板的 **CANVAS** 标签中使用：

- **多画板管理**：画板以独立 JSON 文件存储（`data/graphs/*.json`），支持创建 / 切换 / 重命名 / 删除
- **图谱可视化**：Cytoscape 力导向布局，节点自由拖拽、缩放、平移、自适应居中
- **实体关系编辑**：添加/编辑实体（GraphRAG 描述、属性、文本溯源）、拖拽连线或手动添加关系
- **实体类型管理**：内置 14 类实体（10 类技术情报实体 ThreatActor / Malware / Domain / IP 等 + 4 类社会工程学实体 FraudPattern 骗术模式 / PsychLever 心理杠杆 / ScriptStage 话术阶段 / Persona 冒充角色原型），可自定义类型（名称/标签/颜色/形状）；旧画板打开时自动增量补齐新增内置类型
- **情报下钻**：单击节点查看完整信息，右键展开 1 跳邻居、生成 RAG 上下文、删除节点
- **GraphRAG 检索**：一键生成 1~2 跳子图语义三元组 Prompt Context，导出标准 GraphRAG 索引（兼容 MS GraphRAG / LlamaIndex）
- **保存状态检查**：聊天头部实时显示 `● GRAPH RAG · 画板名`（已保存/已接入）或 `○ 未保存`，画板工具栏显示 `已保存/未保存` 徽标
- **Agent 自动接入**：画板「已保存」后，Agent 可用 `graphrag_status` / `graphrag_query` 回答画板中的实体关系问题；`graph_add_node` / `graph_add_edge` 在画板打开时即可写入（批量沉淀场景：写入会使画板变未保存，属正常，完成后统一保存）

### 11. 项目内技能（Skills）与 MCP 工具

**技能（Skills）**：放在项目内 `skills/` 目录（不再依赖 Claude Code 的 `~/.claude/skills`，可用 `SKILLS_DIR` 环境变量覆盖）。每个技能是一个文件夹 + `SKILL.md`；Agent 先只看到「名称 + description」，命中后才读取正文（渐进式披露）。内置技能：

- `skills/osint-recon/`：面向公开信息收集的情报流程，用户提到“搜集/搜索/查找/调查/情报”等词时触发
- `skills/se-psych-profile/`：社会工程学消息心理画像分析框架（心理杠杆清单/五阶段话术模型/角色原型库），用户粘贴可疑消息样本要求分析时触发

**MCP 工具**：配置文件为项目内 `mcp/mcp.json`（不读 `~/.claude.json` / `claude_desktop_config.json`）。当前已启用并实测可用：

| 服务器 | 命令 | 提供的工具 |
|---|---|---|
| `web` | `uvx mcp-server-fetch` | `web_fetch`（抓取网页正文，默认遵守 robots.txt） |
| `ddg` | `uvx duckduckgo-mcp-server` | `ddg_search` / `ddg_fetch_content` / `ddg_expand_link` |

工具名带服务器前缀（`<server>_<tool>`）。可用 `GET /api/mcp` 查看配置，详见 `mcp/README.md`。

**文件工具**：Agent 使用 `FilesystemBackend`（锚定项目根），因此内置的 `ls / read_file / write_file / edit_file / glob / grep / delete` 全部作用于**真实磁盘**，写入的文件可立即被读取/编辑/检索。

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- Anthropic 兼容 API 凭据（`ANTHROPIC_AUTH_TOKEN` 或 `ANTHROPIC_API_KEY`）

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

模型配置默认读取系统中 `ANTHROPIC_` 开头的环境变量（Claude Code / 智谱等工具设置的凭据可直接复用）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_AUTH_TOKEN` | 认证凭据（Bearer 场景，与 API_KEY 二选一） | （必填） |
| `ANTHROPIC_API_KEY` | 认证凭据（x-api-key 场景） | （必填） |
| `ANTHROPIC_BASE_URL` | API 端点 | `https://api.anthropic.com` |
| `ANTHROPIC_MODEL` | 模型名称 | `claude-sonnet-4-5` |

也可以创建 `.env` 文件覆盖：

```bash
ANTHROPIC_AUTH_TOKEN=your_token_here
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
ANTHROPIC_MODEL=GLM-4.7
```

4. 启动服务（任选一种）：

**方式 A：启动脚本（推荐，自动检查 uv / 凭据 / 依赖）**

```bash
# Windows：双击 start.bat，或在命令行执行
start.bat

# Linux / macOS
chmod +x start.sh   # 首次需要
./start.sh
# 若不想改权限，也可以：bash start.sh
```

脚本可选指定端口：`start.bat 8080` / `./start.sh 8080`。

**方式 B：直接运行**

```bash
uv run python -m web.web_server
```

5. 访问界面：

打开浏览器访问 `http://localhost:8000`

6. 停止服务：

在服务所在的终端按 `Ctrl+C`。如果按了没反应（Windows 上常见：`uv run` 的包装进程会吞掉信号，uvicorn 的 reloader 派生出的 worker 也可能变成孤儿继续占端口）：

```bash
# Windows
stop.bat            # 默认停止 8000 端口；stop.bat 8080 指定端口

# Linux / macOS
./stop.sh           # 或 bash stop.sh
```

> 启动脚本**直接用 `.venv` 里的解释器**（不再套 `uv run`），并**默认关闭热重载（`RELOAD=0`）**。
> 需要热重载时：`set RELOAD=1`（Windows）/ `export RELOAD=1`（Linux/macOS）；
> 直接 `uv run python -m web.web_server` 启动时仍默认开启热重载。

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

### 服务监听与安全

- 服务默认只绑定 `127.0.0.1`（仅本机访问）。需要在局域网访问时设置环境变量 `HOST=0.0.0.0`（注意：`/api/chat` 背后是任意命令执行工具，暴露到局域网前请自行评估风险）
- 可用环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY` | （必填） | 模型认证凭据，缺失时启动直接报错 |
| `HOST` | `127.0.0.1` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `CORS_ORIGINS` | `*` | 允许的跨域来源，逗号分隔；非 `*` 时允许携带凭据 |
| `ALERT_CHECK_INTERVAL` | `30` | 后台告警检查间隔（秒） |
| `RSS_CHECK_INTERVAL` | `10` | 后台 RSS 检查间隔（秒） |

### 模型配置

修改 `model_set/model_set.py` 可以更换模型（或直接通过上述 `ANTHROPIC_*` 环境变量配置）：

```python
model = ChatAnthropic(
    model=model_name,  # ANTHROPIC_MODEL
    api_key=convert_to_secret_str(
        auth_token
    ),  # ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY
    base_url=base_url,  # ANTHROPIC_BASE_URL
)
```

### 工具配置

修改 `agent_set/tools_set.py` 可以添加或修改工具。

### 任务阈值

修改 `web/api/chat_api.py` 中的 `len(message.strip()) >= 20` 可以调整 TODO 创建阈值。

## API 接口

服务提供以下 REST API：

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/` | GET | 返回前端页面 |
| `/alert` | GET | 告警详情页面 |
| `/static/*` | GET | 静态资源 |
| `/api/chat` | POST | 发送聊天消息（SSE 流式） |
| `/api/new` | POST | 创建新对话 |
| `/api/sessions` | GET | 列出所有会话 |
| `/api/history` | GET | 获取对话历史 |
| `/api/history/{tid}` | GET | 获取指定对话 |
| `/api/history/{tid}` | DELETE | 删除对话 |
| `/api/todo` | GET | 获取 TODO 列表 |
| `/api/skills` | GET | 获取可用技能 |
| `/api/tools` | GET | 获取可用工具 |
| `/api/trends` | GET | 获取热门搜索和情报信息 |
| `/api/alerts` | GET/POST | 获取告警规则（含触发次数与最后触发时间统计）/ 创建规则 |
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
| `/api/boards` | GET/POST | 列出所有画板及当前画板 / 创建空画板 |
| `/api/boards/open` | POST | 打开指定画板并载入内存 |
| `/api/boards/rename` | POST | 重命名画板 |
| `/api/boards/{name}` | DELETE | 删除画板（删除当前画板自动切换） |
| `/api/graph` | GET | 读取当前画板图数据 |
| `/api/graph/status` | GET | 当前画板状态（是否已打开/已保存/节点关系数，用于 GraphRAG 接入判定） |
| `/api/types` | GET/POST | 获取全部实体类型 / 新增或更新自定义类型 |
| `/api/types/{type_name}` | DELETE | 删除自定义类型（内置类型不可删） |
| `/api/expand/{node_id}` | GET | 1 跳邻居子图 |
| `/api/node` | POST | 新增 / 更新节点 |
| `/api/node/{node_id}` | DELETE | 删除节点并级联清理关联边 |
| `/api/edge` | POST | 新增 / 更新关系 |
| `/api/save` | POST | 持久化写回当前画板文件 |
| `/api/rag/context/{node_id}` | GET | 提取 1~2 跳子图语义三元组 + 实体描述（Prompt Context） |

## RSS 订阅功能

### 功能说明

- **添加订阅源**：在 INTELLIGENCE 面板的 RSS 标签页，输入 RSS/Atom 订阅地址添加
- **定时抓取**：每个源默认每 60 秒抓取一次（检查间隔 10 秒）；抓取失败同样计入间隔，自动退避，不会对不可用源反复重试
- **实时推送**：只有新出现的文章会通过 SSE 实时推送到前端（按链接去重）
- **文章存储**：每个源保留最近 10 条文章

### 使用示例

添加 RSS 订阅：
```bash
curl -X POST http://localhost:8000/api/rss \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.ruanyifeng.com/blog/atom.xml"}'
```

### 优雅关闭

服务配置了 `timeout_graceful_shutdown=5`（5 秒优雅关闭超时），即使浏览器保持 SSE 长连接，Ctrl+C 后也会在超时后强制退出，不会卡住。

> **停止不掉的兜底**：若 Ctrl+C 无效，执行 `stop.bat` / `./stop.sh`。它会同时结束「占用该端口的进程」和「命令行含 `web.web_server` 的进程」，并在结束后轮询确认端口已释放。

> **热重载说明**：`reload=True` 下修改代码会触发自动重载。由于 SSE 长连接会让旧 worker 无法优雅关闭，优雅关闭超时确保重载在 5 秒内完成，避免服务卡死（历史上曾因 SSE 连接导致重载无限等待、页面转圈）。启动脚本默认 `RELOAD=0`（关闭热重载），以避免 reloader 派生 worker 在异常中断后变成孤儿进程占住端口。

## 性能优化

### 并发与缓存

- **热点数据获取**：使用 `ThreadPoolExecutor` 并发获取多个平台数据，原来串行获取需要约 165 秒，优化后仅需约 2 秒
- **趋势数据缓存**：30 秒 TTL 缓存，API 请求、关联分析和后台告警检查共用一份数据，消除大部分重复外呼
- **真流式响应**：`/api/chat` 基于 `astream_events` 按 token 增量推送，工具调用实时上报
- **历史存储**：对话历史采用 JSONL 追加写入，长会话不再全量重写文件
- **后台任务**：使用 `asyncio.to_thread()` 避免阻塞主事件循环，SSE 事件按连接 fan-out
- **告警匹配优化**：匹配阶段统一预小写、锁外收集命中项，事件创建在锁内串行化（`AlertManager` 线程锁），避免并发写与重复转换
- **SSE 事件单层转发**：广播器发布完整事件消息，SSE 流端点原样转发（修复历史上 alert/rss 事件的二次包装问题）
- **优雅关闭**：服务停止时正确关闭后台任务和线程池，避免 Ctrl+C 卡住

### 技术细节

```python
# trends.py - 并发获取 + TTL 缓存
_executor = ThreadPoolExecutor(max_workers=8)
futures = {_executor.submit(_fetch_platform, p): p for p in platforms}
```

```python
# web_server.py - 异步执行
trends = await asyncio.to_thread(get_trends, check_alerts=True)
```

```python
# web_server.py - 优雅关闭
for task in background_tasks:
    task.cancel()
await asyncio.wait(background_tasks, timeout=3)
shutdown_executor()
```

## 测试

```bash
uv run pytest
```

覆盖 TODO Markdown 解析、告警关键词匹配/去重、RSS/Atom 解析、MCP 配置解析、技能目录规范等纯函数逻辑（当前 66 项）。

## 常见问题

### Q: API Key 如何获取？

A: 支持 Anthropic 协议的平台均可（Anthropic 官方、智谱 open.bigmodel.cn 等）。本机若已配置过 `ANTHROPIC_AUTH_TOKEN` 等环境变量（如 Claude Code），可直接复用。

### Q: 为什么工具调用失败？

A: 检查 PowerShell 是否可用，以及命令是否有权限执行。

### Q: 聊天没有回答 / 提示 401？

A: 模型认证失败。请确认启动服务时使用的是真实 `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY`（不要在启动命令里覆盖成占位符），或创建 `.env` 文件配置后重启。画板功能（画布/保存/GraphRAG 接入徽标）不依赖模型凭据，但 Agent 对话需要有效凭据。

### Q: 按 Ctrl+C 停不掉服务？

A: Windows 上常见，原因是多了一层进程：`uv run` 的包装进程会吞掉 Ctrl+C；uvicorn 的 `reload=True` 会派生 worker，父进程被打断后 worker 可能变成孤儿（端口 owner 指向已死的父 PID）。处理方式：

1. 用启动脚本（`start.bat` / `start.sh`）——它们直接调用 `.venv` 的解释器，且默认 `RELOAD=0`；
2. 仍然停不掉时执行 `stop.bat` / `./stop.sh`：它会按「端口占用者 + 命令行含 web.web_server」双重规则结束进程，并确认端口已释放。

### Q: 前端什么都不显示 / 看不到回答？

A: 现在后端错误（401、超时等）会在聊天区以红色 `错误: ...` 明确显示，不会再静默无反应。若看到 401，请检查启动服务的终端里 `ANTHROPIC_AUTH_TOKEN` 是否有效（不要用占位符启动）。

### Q: 如何修改模型？

A: 修改 `model_set/model_set.py` 或设置 `ANTHROPIC_MODEL` / `ANTHROPIC_BASE_URL` 环境变量，支持 Anthropic 兼容的 API。

### Q: 前端侧边栏如何调整宽度？

A: 将鼠标移动到侧边栏边缘，出现双箭头光标后拖动即可。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [Anthropic Claude](https://www.anthropic.com/) - 大语言模型 API 协议
- [DeepAgents](https://github.com/deepagents) - Agent 框架
- 微博/百度/头条/B站/抖音 - 热搜榜单数据源
- [HackerNews API](https://github.com/HackerNews/API) - 科技新闻数据源
