"""
========================================
MCP Set - MCP 服务器配置模块
========================================
功能: 从项目内 mcp/mcp.json 读取 MCP 服务器配置，
不读取 Claude Code / Claude Desktop 的全局配置
 作者: CuteCuteYu
"""

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 配置路径（项目内，独立于任何外部工具的全局配置）
# ═══════════════════════════════════════════════════════════════

# 项目根目录（agent_set/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# MCP 配置目录：默认项目内 mcp/，可用环境变量 MCP_DIR 覆盖
MCP_DIR = Path(os.environ.get("MCP_DIR") or (_PROJECT_ROOT / "mcp"))

# MCP 配置文件
MCP_CONFIG_PATH = MCP_DIR / "mcp.json"

# 支持的传输方式（"http" 是 "streamable_http" 的别名，写入配置时两者均可）
SUPPORTED_TRANSPORTS = ("stdio", "sse", "streamable_http", "websocket")

# MCP 工具加载超时（秒）：避免某个服务器无响应时阻塞 Agent 启动
MCP_LOAD_TIMEOUT = float(os.environ.get("MCP_LOAD_TIMEOUT", "20"))


# ═══════════════════════════════════════════════════════════════
# 配置加载
# ═══════════════════════════════════════════════════════════════


def load_mcp_config() -> dict:
    """
    读取项目内 MCP 配置

    配置缺失或格式非法时返回空配置（不会抛异常，保证启动流程不受影响）。

    返回:
        {"mcpServers": {名称: 配置字典}}
    """
    empty: dict = {"mcpServers": {}}

    if not MCP_CONFIG_PATH.exists():
        logger.debug("未找到 MCP 配置文件: %s", MCP_CONFIG_PATH)
        return empty

    try:
        data = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("MCP 配置读取失败: %s", MCP_CONFIG_PATH, exc_info=True)
        return empty

    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        logger.warning("MCP 配置格式不合法（缺少 mcpServers 对象）: %s", MCP_CONFIG_PATH)
        return empty

    return {"mcpServers": servers}


def _infer_transport(config: dict) -> str:
    """根据配置字段推断传输方式（未显式声明时）"""
    transport = config.get("transport")
    if isinstance(transport, str) and transport:
        return transport
    if config.get("command"):
        return "stdio"
    if config.get("url"):
        return "http"
    return "unknown"


def list_mcp_servers() -> list[dict]:
    """
    列出已配置的 MCP 服务器摘要（仅解析配置，不建立连接）

    返回:
        服务器列表，每项包含 name / transport / enabled / target
    """
    servers = load_mcp_config()["mcpServers"]
    result: list[dict] = []

    for name, config in servers.items():
        if not isinstance(config, dict):
            logger.warning("MCP 服务器 %s 的配置不是对象，已跳过", name)
            continue
        result.append(
            {
                "name": name,
                "transport": _infer_transport(config),
                "enabled": bool(config.get("enabled", True)),
                "target": config.get("command") or config.get("url") or "",
            }
        )

    return sorted(result, key=lambda item: item["name"])


def enabled_mcp_servers() -> dict[str, dict]:
    """
    返回已启用的 MCP 服务器配置（供后续建立连接时使用）

    返回:
        {名称: 配置字典}，仅包含 enabled 非 False 的条目
    """
    servers = load_mcp_config()["mcpServers"]
    return {
        name: config
        for name, config in servers.items()
        if isinstance(config, dict) and config.get("enabled", True)
    }


# ═══════════════════════════════════════════════════════════════
# 连接构建与工具加载
# ═══════════════════════════════════════════════════════════════


def _normalize_transport(config: dict) -> str:
    """归一化传输方式（http -> streamable_http）"""
    transport = _infer_transport(config)
    return "streamable_http" if transport == "http" else transport


def _build_connection(config: dict) -> dict | None:
    """
    把项目配置转换为 langchain-mcp-adapters 的 Connection 结构

    参数:
        config: mcp.json 中的单个服务器配置

    返回:
        Connection 字典；配置不完整时返回 None（调用方应跳过该服务器）
    """
    transport = _normalize_transport(config)

    if transport == "stdio":
        command = config.get("command")
        if not command:
            return None
        connection: dict = {
            "transport": "stdio",
            "command": command,
            "args": list(config.get("args") or []),
        }
        if config.get("env"):
            connection["env"] = {str(k): str(v) for k, v in config["env"].items()}
        if config.get("cwd"):
            connection["cwd"] = config["cwd"]
        return connection

    if transport in ("sse", "streamable_http", "websocket"):
        url = config.get("url")
        if not url:
            return None
        connection = {"transport": transport, "url": url}
        if config.get("headers"):
            connection["headers"] = dict(config["headers"])
        return connection

    logger.warning("不支持的 MCP 传输方式: %s", transport)
    return None


def build_connections() -> dict[str, dict]:
    """
    构建所有已启用服务器的连接配置

    返回:
        {服务器名: Connection 字典}，跳过配置不完整的条目
    """
    connections: dict[str, dict] = {}
    for name, config in enabled_mcp_servers().items():
        connection = _build_connection(config)
        if connection is None:
            logger.warning("MCP 服务器 %s 配置不完整，已跳过", name)
            continue
        connections[name] = connection
    return connections


async def _load_mcp_tools_async(timeout: float) -> list:
    """异步加载所有 MCP 工具（超时上限 timeout 秒）"""
    connections = build_connections()
    if not connections:
        return []

    # 惰性导入：未配置 MCP 时完全不依赖该包
    from langchain_mcp_adapters.client import MultiServerMCPClient

    # tool_name_prefix=True：工具名加服务器前缀，避免与其他工具重名被覆盖
    client = MultiServerMCPClient(connections, tool_name_prefix=True)
    return await asyncio.wait_for(client.get_tools(), timeout=timeout)


def create_mcp_tools(timeout: float | None = None) -> list:
    """
    按项目配置加载 MCP 工具（best-effort）

    无配置或加载失败（含超时）时返回空列表，绝不抛异常，
    保证 Agent 在 MCP 服务器不可用时仍能正常启动。

    参数:
        timeout: 加载超时秒数，默认 MCP_LOAD_TIMEOUT

    返回:
        LangChain 工具列表
    """
    if not enabled_mcp_servers():
        return []

    timeout = MCP_LOAD_TIMEOUT if timeout is None else timeout

    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # 无运行中的事件循环，直接执行
            tools = asyncio.run(_load_mcp_tools_async(timeout))
        else:
            # 已有事件循环（如在异步上下文里构建 Agent）：放到独立线程中执行
            with ThreadPoolExecutor(max_workers=1) as executor:
                tools = executor.submit(
                    lambda: asyncio.run(_load_mcp_tools_async(timeout))
                ).result()
    except Exception:
        # best-effort：任何失败都不应中断 Agent 启动
        logger.warning("MCP 工具加载失败，已跳过", exc_info=True)
        return []

    logger.info("已加载 %d 个 MCP 工具", len(tools))
    return tools
