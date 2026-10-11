"""MCP 配置加载测试（项目内独立配置，不依赖任何外部工具的全局文件）"""

import json

from agent_set import mcp_set


def test_missing_config_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_set, "MCP_CONFIG_PATH", tmp_path / "not-exist.json")
    assert mcp_set.load_mcp_config() == {"mcpServers": {}}
    assert mcp_set.list_mcp_servers() == []
    assert mcp_set.enabled_mcp_servers() == {}


def test_malformed_json_returns_empty(tmp_path, monkeypatch):
    config_file = tmp_path / "mcp.json"
    config_file.write_text("{ not valid json", encoding="utf-8")
    monkeypatch.setattr(mcp_set, "MCP_CONFIG_PATH", config_file)
    assert mcp_set.load_mcp_config() == {"mcpServers": {}}


def test_non_object_servers_returns_empty(tmp_path, monkeypatch):
    config_file = tmp_path / "mcp.json"
    config_file.write_text(json.dumps({"mcpServers": ["bad"]}), encoding="utf-8")
    monkeypatch.setattr(mcp_set, "MCP_CONFIG_PATH", config_file)
    assert mcp_set.load_mcp_config() == {"mcpServers": {}}


def test_servers_parsed_and_sorted(tmp_path, monkeypatch):
    config_file = tmp_path / "mcp.json"
    config_file.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "web": {"url": "https://example.com/mcp", "enabled": False},
                    "fs": {"command": "npx", "args": ["-y", "server-fs"]},
                    "bad": "not-a-dict",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mcp_set, "MCP_CONFIG_PATH", config_file)

    servers = {item["name"]: item for item in mcp_set.list_mcp_servers()}
    assert list(servers) == ["fs", "web"]  # 非字典条目被跳过，且按名称排序
    assert servers["fs"]["transport"] == "stdio"
    assert servers["fs"]["enabled"] is True
    assert servers["fs"]["target"] == "npx"
    assert servers["web"]["transport"] == "http"
    assert servers["web"]["enabled"] is False

    # 仅返回已启用的服务器
    assert set(mcp_set.enabled_mcp_servers()) == {"fs"}


def test_default_config_path_is_project_local():
    # 默认配置必须位于项目内，不得指向 Claude Code/Desktop 的全局配置
    path = str(mcp_set.MCP_CONFIG_PATH).replace("\\", "/")
    assert path.endswith("/mcp/mcp.json")
    assert ".claude" not in path


def test_build_connections_maps_transports(tmp_path, monkeypatch):
    config_file = tmp_path / "mcp.json"
    config_file.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "fs": {"command": "npx", "args": ["-y", "server-fs"], "env": {"A": 1}},
                    "web": {"url": "https://example.com/mcp"},  # 省略 transport -> 推断为 http
                    "sse_srv": {"transport": "sse", "url": "https://example.com/sse"},
                    "off": {"command": "x", "enabled": False},
                    "broken": {"transport": "stdio"},  # 缺 command -> 跳过
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mcp_set, "MCP_CONFIG_PATH", config_file)

    connections = mcp_set.build_connections()
    assert set(connections) == {"fs", "web", "sse_srv"}

    assert connections["fs"]["transport"] == "stdio"
    assert connections["fs"]["args"] == ["-y", "server-fs"]
    assert connections["fs"]["env"] == {"A": "1"}  # env 值统一转字符串

    # 未声明 transport 但有 url -> 归一化为 streamable_http（http 的别名）
    assert connections["web"]["transport"] == "streamable_http"
    assert connections["sse_srv"]["transport"] == "sse"


def test_create_mcp_tools_empty_when_not_configured(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_set, "MCP_CONFIG_PATH", tmp_path / "none.json")
    # 无配置时必须直接返回空列表，且不导入/不连接任何 MCP 服务
    assert mcp_set.create_mcp_tools() == []
