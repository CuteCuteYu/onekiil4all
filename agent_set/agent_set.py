"""
========================================
Agent Set - Agent配置模块
========================================
功能: 创建和配置AI Agent
整合模型、工具、技能和记忆系统
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════
# 导入DeepAgents框架和LangChain组件
# ═══════════════════════════════════════════════════════════════

import threading
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend
from langgraph.checkpoint.memory import InMemorySaver

from model_set import model_set  # 模型配置

# ═══════════════════════════════════════════════════════════════
# 导入项目内部模块
# ═══════════════════════════════════════════════════════════════
from . import workspace
from .mcp_set import create_mcp_tools  # MCP 工具加载
from .tools import tools as project_tools  # 项目工具列表

# ═══════════════════════════════════════════════════════════════
# 路径与资源常量
# ═══════════════════════════════════════════════════════════════

# 项目根目录（agent_set/ 的上一级），锚定根目录避免依赖启动时的工作目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 系统提示词文件（虚拟路径，由 CompositeBackend 路由到 <项目根>/prompt/AGENTS.md）
MEMORY_FILES = ["/prompt/AGENTS.md"]

# 技能目录（虚拟路径，路由到 <项目根>/skills/）
SKILLS_PATH = "/skills/"

# ═══════════════════════════════════════════════════════════════
# Agent 实例缓存（按工作区路径缓存，切换工作区后自动重建）
# ═══════════════════════════════════════════════════════════════

_agent_lock = threading.Lock()
_agent_cache: dict[str, object] = {}


# ═══════════════════════════════════════════════════════════════
# Agent创建函数
# ═══════════════════════════════════════════════════════════════


def create_agent():
    """
    创建配置好的Agent实例（需先选择工作区）

    整合以下组件：
    - AI模型 (DeepSeek)
    - 工具集 (项目工具 + MCP 工具)
    - 技能集 (项目内 skills/，从真实磁盘读取)
    - 记忆系统 (InMemorySaver用于检查点)
    - 系统提示词 (prompt/AGENTS.md，从真实磁盘读取)
    - 文件系统后端 (CompositeBackend)：
        * 默认根 = 用户选择的工作区文件夹，Agent 的所有产物默认保存到这里
          （virtual_mode 阻断 .. / ~ / 越界绝对路径）
        * /prompt/ 路由到 <项目根>/prompt/（系统提示词所在）
        * /skills/ 路由到 <项目根>/skills/（技能所在）

    返回:
        配置好的Agent实例

    异常:
        RuntimeError: 尚未选择工作区
    """
    ws = workspace.get_workspace()
    if ws is None:
        raise RuntimeError("尚未选择工作区，无法创建 Agent")

    # MCP 工具为 best-effort：无配置或加载失败时返回空列表，不影响启动
    mcp_tools = create_mcp_tools()

    agent = create_deep_agent(
        model=model_set.model,  # 使用配置的DeepSeek模型
        memory=list(MEMORY_FILES),  # 系统提示词文件（真实磁盘 prompt/AGENTS.md）
        backend=CompositeBackend(
            default=FilesystemBackend(
                root_dir=ws, virtual_mode=True
            ),  # 工作区为默认根：所有产物落在这里
            routes={
                # 路由前缀会被剥离后再转发，因此后端根目录要对应到子目录
                "/prompt/": FilesystemBackend(
                    root_dir=_PROJECT_ROOT / "prompt", virtual_mode=True
                ),
                "/skills/": FilesystemBackend(
                    root_dir=_PROJECT_ROOT / "skills", virtual_mode=True
                ),
            },
        ),
        skills=[SKILLS_PATH],  # 技能路径（真实磁盘 skills/）
        tools=[*project_tools, *mcp_tools],  # 项目工具 + MCP 工具
        checkpointer=InMemorySaver(),  # 内存检查点保存
    )
    return agent


def get_agent():
    """
    获取当前工作区对应的Agent实例（带缓存）

    工作区切换后（路径变化）自动重建 Agent；
    同一工作区内复用缓存实例，避免重复加载 MCP 工具。

    返回:
        Agent实例

    异常:
        RuntimeError: 尚未选择工作区
    """
    ws = workspace.get_workspace()
    if ws is None:
        raise RuntimeError("尚未选择工作区，请先在页面选择工作区文件夹")

    key = str(ws)
    with _agent_lock:
        if key not in _agent_cache:
            _agent_cache[key] = create_agent()
        return _agent_cache[key]
