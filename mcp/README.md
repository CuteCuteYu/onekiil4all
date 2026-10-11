# MCP 配置（项目内独立设置）

本目录存放**本项目专属**的 MCP 服务器配置，**不读取** Claude Code / Claude Desktop 的全局配置
（如 `~/.claude.json`、`claude_desktop_config.json`）。

读取逻辑见 `agent_set/mcp_set.py`：
- 配置文件：`mcp/mcp.json`（可用环境变量 `MCP_DIR` 指定其他目录）
- 服务器工具会在 Agent 启动时自动挂载（见下文「当前状态」）

## 已配置的服务器（均已在本机实测通过）

| 服务器 | 启动命令 | 提供的工具 | 说明 |
|---|---|---|---|
| `web` | `uvx mcp-server-fetch` | `web_fetch` | 官方参考服务器：抓取 URL 并转为 Markdown（补充搜索后的正文采集） |
| `ddg` | `uvx duckduckgo-mcp-server` | `ddg_search` / `ddg_fetch_content` / `ddg_expand_link` | DuckDuckGo 搜索 + 正文抓取 + 短链展开（无需 API Key） |

> 工具名带服务器前缀（`<server>_<tool>`）。实测样例：`ddg_search("openai")` 返回 10 条结果；
> `web_fetch("https://example.com")` 返回页面正文。

> ⚠️ `web`（mcp-server-fetch）默认**遵守目标站点的 robots.txt**；被站点禁止自动抓取时会拒绝并说明原因。
> 如需放宽，可在 `args` 里加 `--ignore-robots-txt`（请自行确保合规与授权）。

## 文件格式

```json
{
  "mcpServers": {
    "<server-name>": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["<pypi-package-or-command>"],
      "env": { "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple" },
      "enabled": true
    },
    "<http-server>": {
      "transport": "streamable_http",
      "url": "https://example.com/mcp",
      "headers": { "Authorization": "Bearer xxx" },
      "enabled": false
    }
  }
}
```

### 字段说明

| 字段 | 适用传输 | 说明 |
|---|---|---|
| `transport` | 全部 | `stdio` / `sse` / `streamable_http` / `websocket`。省略时按 `command`→`stdio`、`url`→`streamable_http` 推断；`http` 是 `streamable_http` 的别名 |
| `command` / `args` / `env` / `cwd` | stdio | 启动命令、参数、额外环境变量与工作目录 |
| `url` / `headers` | sse / http | 服务地址与请求头 |
| `enabled` | 全部 | 默认 `true`；设为 `false` 可暂时停用而不删除配置 |

> ⚠️ 不要把密钥写进本文件并提交到版本库；建议用环境变量占位或在本地忽略该文件。

## 当前状态

**已接入**：Agent 启动时会读取本文件，连接所有 `enabled` 的服务器，并把其工具挂到 Agent 上
（见 `agent_set/mcp_set.py` → `create_mcp_tools()`，在 `agent_set/agent_set.py` 中与项目工具合并）。

- 工具名会加上服务器前缀（`<server>_<tool>`）以避免重名与项目工具冲突
- MCP 工具是**异步**的，通过 Agent 的异步执行链（`astream_events`）调用
- 加载是 **best-effort**：服务器不可用/超时（`MCP_LOAD_TIMEOUT`，默认 20s）只会跳过，不会阻断 Agent 启动
- 每次工具调用都会新建一次会话（适配器行为），因此无长连接状态

调试用：`GET /api/mcp` 返回解析后的服务器列表（名称 / 传输方式 / 是否启用 / 目标）。

## 国内网络注意事项

1. **Python 服务器（`uvx`）**：在 `env` 里设 `UV_DEFAULT_INDEX` 指向国内镜像（本项目用清华 TUNA），
   否则 uv 解析依赖可能长时间卡住。`env` 是**叠加**在默认环境上的（`{**默认环境, **你的env}`），
   不会覆盖 `PATH`，可放心只写镜像变量。
2. **Node 服务器（`npx`）**：npm 建议指向国内镜像 `npm config set registry https://registry.npmmirror.com`。
   另外 Windows 上 `subprocess` **不解析 `.cmd`**，若用 npm 服务器，`command` 要写 `npx.cmd`（而不是 `npx`）。
3. **可用性因网络环境而异**：本文件中的服务器是在**本机实测通过**后才加入的。
   新增服务器时请先单独验证能否启动并调用成功，再写进 `mcp.json`；
   不可用时 `create_mcp_tools()` 只会跳过（best-effort），不会影响 Agent 启动。

## 可选：已实测但暂未启用

- `mcp-server-git`（`uvx mcp-server-git`）：提供 12 个 git 工具（`git_status` / `git_log` / `git_show` 等），
  适合对已克隆的目标仓库做源码侦察。工具数量较多，按需再启用：

```json
"git": {
  "transport": "stdio",
  "command": "uvx",
  "args": ["mcp-server-git"],
  "env": { "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple" },
  "enabled": true
}
```

> 已实测**不可用/不存在**的候选（不用再试）：`mcp-whois`、`whois-mcp`、`whois-mcp-server`、
> `mcp-server-dns`、`dns-mcp-server`（PyPI 上均无此包）。DNS/WHOIS 类如需使用，建议自家写一个本地 stdio 服务器。
