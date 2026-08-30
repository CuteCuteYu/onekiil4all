# GraphRAG Viz · 情报分析图谱

纯本地轻量运行的知识图谱可视化 + GraphRAG 数据准备系统（类似 Maltego + 知识图谱编辑器）。

将收集到的情报实体与关系可视化、自由拖拽下钻分析，并导出为兼容主流 GraphRAG（MS GraphRAG / LlamaIndex）的知识索引结构，可直接用于真实检索问答。

## 核心特性

| 特性 | 说明 |
| --- | --- |
| 🎨 黑色线条主题 | 纯黑背景 + 线稿风格（Wireframe Noir）：节点透明填充 + 彩色线条描边、细线边、细边框 UI |
| 📁 多画板管理 | 画板以独立文件管理（`graphs/*.json`）：进入时选择或创建画板，支持重命名 / 删除（删除当前画板自动切换） |
| 🖱 画布交互 | cose 力导向布局，节点自由拖拽、缩放、平移、自适应居中 |
| 🔗 拖拽连线 | 长按节点拖动直接拖出箭头连线到目标实体，松手弹出关系创建对话框（源 / 目标自动预填） |
| 🏷 类型区分 | ThreatActor / Malware / Tool / Domain / IP / Vulnerability / Organization / Email / Hash / URL 十类情报实体，自动配色 + 形状区分 |
| ⚙ 自定义实体类型 | 「类型管理」面板自定义实体类型（类型名 / 标签 / 颜色 / 形状），持久化保存，内置类型受保护 |
| ✎ 编辑实体 | 抽屉面板「✎ 编辑」修改已有实体的名称、类型、描述、属性与溯源 |
| 🔍 情报下钻 | 单击节点查看完整信息（GraphRAG 描述、属性、关联关系、文本溯源）；右键展开邻居（1-Hop Expand） |
| 🧠 RAG 上下文 | 一键生成指定节点的 1~2 跳子图语义三元组 + 实体描述 Prompt Context |
| 📤 GraphRAG 导出 | 一键下载标准 JSON 索引（entities / relationships 分组，兼容 MS GraphRAG 与 LlamaIndex） |
| 💾 持久化 | 「保存到本地」将内存图数据原子写回当前画板文件 |

## 技术栈

- **后端**：Python（FastAPI + NetworkX）
- **存储**：画板以独立文件管理（`graphs/*.json`），启动载入内存，变动时按需保存，无外部数据库
- **前端**：单文件 HTML/JS（CDN 引入 Cytoscape.js + Tailwind CSS，无需 Node.js 打包）
- **环境管理**：uv（`pyproject.toml` / `uv.lock`），另附 `requirements.txt` 兼容文件
- **LLM（可选）**：Anthropic 兼容 API（用于 GraphRAG 真实验证）

## 项目结构

```
test/
├── main.py              # FastAPI 服务端（画板管理 / 图谱 CRUD / RAG 上下文 / 静态托管）
├── verify_graphrag.py   # GraphRAG 可用性验证脚本（真实调用 LLM 跑局部查询）
├── graph_data.json      # 旧版单文件数据（启动时自动迁移为「默认画板」）
├── graphs/              # 画板目录：每个画板一个独立 JSON 文件
│   ├── 默认画板.json     # 初始 APT29 情报数据（10 节点 / 12 关系）
│   └── *.json           # 用户创建的其他画板
├── static/
│   └── index.html       # 单文件前端（Cytoscape + Tailwind，黑色线条主题）
├── .agents/
│   └── skills/
│       └── graphrag-board/   # AI 对话生成画板 skill（SKILL.md + 规范 + 示例）
├── requirements.txt     # 极简依赖（兼容 pip）
├── pyproject.toml       # uv 项目配置
└── uv.lock              # uv 依赖锁文件
```

## 快速启动

```bash
# 1. 安装依赖（uv 方式，推荐）
uv sync

# 2. 启动服务
uv run uvicorn main:app --host 127.0.0.1 --port 8000

# 3. 浏览器打开
#    http://127.0.0.1:8000
```

> 不使用 uv 时：`pip install -r requirements.txt` 后执行 `uvicorn main:app --reload` 即可。

## 环境变量（GraphRAG 真实验证用）

`verify_graphrag.py` 通过 Anthropic 兼容 API 调用 LLM，读取以下环境变量：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `ANTHROPIC_BASE_URL` | Anthropic 兼容 API 地址 | `https://open.bigmodel.cn/api/anthropic` |
| `ANTHROPIC_AUTH_TOKEN` | API 认证令牌（`x-api-key` 头） | `xxxxx.yyyyy` |
| `ANTHROPIC_MODEL` | 模型名称 | `GLM-4.7` |

## AI 对话生成画板（graphrag-board skill）

项目内置 `graphrag-board` skill，让 AI 理解 GraphRAG 画板数据规范——用户只需用自然语言描述情报内容，AI 即可自动生成符合规范的画板数据并保存到 `graphs/`，随后可在前端直接打开使用。

### Skill 结构

```
.agents/skills/graphrag-board/
├── SKILL.md                    # 主说明：触发条件、生成流程、保存位置、验证方法
└── references/
    ├── schema.md               # 数据规范：字段说明、10 类类型体系、关系动词约定
    └── example.json            # 完整示例（APT29 画板，5 节点 / 5 边）
```

### 数据规范要点

**节点（Entities）**：`id` / `name` / `type` / `description` / `properties` / `source_chunks`

**边（Relationships）**：`id` / `source` / `target` / `relation`（大写下划线动词）/ `description` / `weight`（0.0~1.0）

**类型体系**：ThreatActor / Malware / Tool / Domain / IP / Vulnerability / Organization / Email / Hash / URL（可自定义）

### 使用方式

直接对 AI 用自然语言描述情报内容即可，例如：

> "帮我创建一个关于 Lazarus 组织的画板，包含它的恶意软件、C2 域名和利用的漏洞"

AI 会按 skill 规范执行：

1. 从对话中提取情报实体与关系
2. 按规范生成画板 JSON（含 `types` / `nodes` / `edges`）
3. 保存到 `graphs/{画板名}.json`
4. 校验 JSON 格式合法性

### 验证

生成后 AI 会运行 JSON 校验确认数据合法，也可手动执行：

```bash
uv run python -c "import json; d=json.load(open('graphs/画板名.json', encoding='utf-8')); print('OK', len(d['nodes']), 'nodes', len(d['edges']), 'edges')"
```

### 实测示例

通过对话生成的「Lazarus 演示」画板（6 节点 / 5 边）已成功被系统加载并在前端渲染：

| 实体 | 类型 | 关系 |
| --- | --- | --- |
| Lazarus Group | ThreatActor | CONTROLS HWA Door / USES AppleJeus / EXPLOITS Log4Shell |
| HWA Door | Malware | RESOLVES_TO update-cdn[.]net |
| AppleJeus | Malware | — |
| update-cdn[.]net | Domain | RESOLVES_TO 45.155.205.233 |
| 45.155.205.233 | IP | — |
| CVE-2021-44228 (Log4Shell) | Vulnerability | — |

## 使用指南

### 1. 画板管理
- 进入系统后选择已有画板继续编辑，或输入名称创建全新空画板
- 顶部「📁 当前画板」按钮随时切换 / 新建 / 删除画板

### 2. 添加情报实体
- 工具栏「＋ 添加实体」：填写名称、类型、GraphRAG 描述、属性（JSON）、文本溯源
- 工具栏「⚙ 类型管理」：自定义实体类型（类型名 / 标签 / 颜色 / 形状）

### 3. 建立关系（两种方式）
- **拖拽连线**：长按源节点（>300ms）拖动拖出箭头，松手到目标节点，弹出对话框填写关系动词
- **手动添加**：工具栏「⇄ 添加关系」，选择源 / 目标节点并填写关系

### 4. 情报下钻分析
- **单击节点**：右侧抽屉展示完整情报（描述、属性、关联关系、文本溯源）
- **右键节点**：展开邻居（1-Hop Expand）、生成 RAG 上下文、删除节点
- **🧠 RAG 上下文**：生成 1~2 跳子图的语义三元组 Prompt Context

### 5. 导出与保存
- **⬇ 导出 GraphRAG 索引**：下载标准 JSON（entities / relationships 分组）
- **💾 保存到本地**：持久化写回当前画板文件

## API 规范

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/boards` | 列出所有画板及当前画板 |
| POST | `/api/boards` | 创建全新的空画板 |
| POST | `/api/boards/open` | 打开指定画板并载入内存 |
| POST | `/api/boards/rename` | 重命名画板 |
| DELETE | `/api/boards/{name}` | 删除画板（删除当前画板自动切换） |
| GET | `/api/graph` | 读取当前画板图数据 |
| GET | `/api/types` | 获取全部实体类型定义（内置 + 自定义） |
| POST | `/api/types` | 新增 / 更新自定义实体类型（名称 / 标签 / 颜色 / 形状） |
| DELETE | `/api/types/{type_name}` | 删除自定义实体类型（内置类型不可删除） |
| GET | `/api/expand/{node_id}` | NetworkX 检索 1 跳邻居子图 |
| POST | `/api/node` | 新增 / 更新节点（含 description 字段） |
| DELETE | `/api/node/{node_id}` | 删除节点并级联清理关联边 |
| POST | `/api/edge` | 新增 / 更新关系 |
| POST | `/api/save` | 全量持久化写回当前画板文件 |
| GET | `/api/rag/context/{node_id}` | 提取 1~2 跳子图语义三元组与实体描述，拼接 Prompt Context |

## 数据模型（GraphRAG 规范）

**节点（Entities）**：`id` / `name` / `type` / `description` / `properties` / `source_chunks`

**边（Relationships）**：`id` / `source` / `target` / `relation`（大写下划线动词）/ `description` / `weight`（0.0~1.0）

**类型（Types）**：`name` / `label` / `color` / `shape` / `builtin`（内置类型不可删除，自定义类型可增删）

初始数据以 APT29 攻击链为蓝本（10 节点 / 12 关系），`source_chunks` 引用情报报告片段作为文本溯源。

### GraphRAG 索引导出格式

```json
{
  "graph_name": "情报分析图谱",
  "exported_at": "2026-08-30T22:36:00",
  "entities": [
    { "id": "ent_apt29", "name": "APT29", "type": "ThreatActor",
      "description": "…", "properties": {…}, "source_chunks": ["report_001: …"] }
  ],
  "relationships": [
    { "id": "rel_apt29_controls_beacon", "source": "ent_apt29",
      "target": "ent_malware_beacon", "relation": "CONTROLS",
      "description": "…", "weight": 0.95 }
  ],
  "graphrag_compat": {
    "ms_graphrag": "entities 对应 entity 表，relationships 对应 relationship 表，source_chunks 对应 text_unit 关联",
    "llamaindex": "每条 relationship 可转换为 (head, relation, tail) 三元组"
  }
}
```

## GraphRAG 可用性验证（真实跑通）

`verify_graphrag.py` 用保存的图数据（`graphs/默认画板.json`）真实跑 GraphRAG 局部查询：
实体识别（LLM）→ 子图检索（NetworkX 1~2 跳）→ 上下文拼接 → LLM 生成回答。

```bash
uv run python verify_graphrag.py
```

LLM 通过 Anthropic 兼容 API 调用，读取环境变量：
`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL`（当前为智谱 GLM-4.7）。

**实测结果**（GLM-4.7）：

| 问题 | 回答 |
| --- | --- |
| APT29 使用哪些恶意软件和工具？ | Cobalt Strike Beacon、鱼叉式钓鱼邮件、PowerShell Empire |
| Cobalt Strike Beacon 通过什么域名和 IP 通信？ | cdn-command[.]com → 185.220.101.34 |
| Zerologon 漏洞被谁利用？它影响什么？ | 被 APT29 利用，影响 Windows 域控制器 |

三个查询均基于图谱上下文准确回答，验证了导出的 GraphRAG 索引可直接用于真实检索问答。

## 验证清单

1. `uv sync` 安装依赖成功
2. `uv run uvicorn main:app --host 127.0.0.1 --port 8000` 启动无报错
3. 浏览器打开 `http://127.0.0.1:8000`，画布渲染 10 节点 / 12 关系
4. 拖拽 / 缩放 / 平移正常；单击节点抽屉显示完整信息
5. 右键展开邻居合并新节点；删除节点画布 + 内存同步移除
6. 长按节点拖动拖出箭头，松手到目标节点弹出关系对话框（源 / 目标预填）
7. 添加实体 / 关系后「保存到本地」，重启服务数据仍在
8. 导出 GraphRAG 索引 JSON 结构符合规范
9. `curl http://127.0.0.1:8000/api/rag/context/ent_apt29` 返回完整 Prompt Context
10. `uv run python verify_graphrag.py` 真实跑通 GraphRAG 检索问答

## 注意事项

- **删除节点 / 画板**：仅作用于内存与文件，删除画板不可恢复，操作前有确认提示
- **保存时机**：编辑操作（添加 / 删除 / 修改）默认只改内存，需点「💾 保存到本地」才落盘
- **PowerShell 中文编码**：在 Windows PowerShell 中测试中文画板名等接口时，建议使用 `curl.exe` 或 UTF-8 编码，避免乱码
- **LLM 依赖**：`verify_graphrag.py` 需要配置 `ANTHROPIC_*` 环境变量；未配置时仅前端 RAG 上下文（`/api/rag/context`）可用，无需 LLM