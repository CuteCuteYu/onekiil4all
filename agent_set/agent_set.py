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

from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import InMemorySaver

from model_set import model_set  # 模型配置

# ═══════════════════════════════════════════════════════════════
# 导入项目内部模块
# ═══════════════════════════════════════════════════════════════
from .mcp_set import create_mcp_tools  # MCP 工具加载
from .tools import tools as project_tools  # 项目工具列表

# ═══════════════════════════════════════════════════════════════
# 路径与资源常量
# ═══════════════════════════════════════════════════════════════

# 项目根目录（agent_set/ 的上一级），锚定根目录避免依赖启动时的工作目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 系统提示词文件（虚拟路径，由 FilesystemBackend 映射到 <项目根>/prompt/AGENTS.md）
MEMORY_FILES = ["/prompt/AGENTS.md"]

# 技能目录（虚拟路径，映射到 <项目根>/skills/）
SKILLS_PATH = "/skills/"


# ═══════════════════════════════════════════════════════════════
# Agent创建函数
# ═══════════════════════════════════════════════════════════════


def create_agent():
    """
    创建配置好的Agent实例

    整合以下组件：
    - AI模型 (DeepSeek)
    - 工具集 (项目工具 + MCP 工具)
    - 技能集 (项目内 skills/，从真实磁盘读取)
    - 记忆系统 (InMemorySaver用于检查点)
    - 系统提示词 (prompt/AGENTS.md，从真实磁盘读取)
    - 文件系统后端 (FilesystemBackend，锚定项目根目录)

    说明:
        使用 FilesystemBackend 后，Agent 内置的文件工具
        (ls/read_file/write_file/edit_file/delete/glob/grep) 全部作用于真实磁盘，
        路径以项目根目录为虚拟根（virtual_mode 阻断 ../~ 逃逸），
        因此「写入的文件」能被「读取/编辑/列举」一致地看到，便于管理已有文件。

    返回:
        配置好的Agent实例
    """
    # MCP 工具为 best-effort：无配置或加载失败时返回空列表，不影响启动
    mcp_tools = create_mcp_tools()

    agent = create_deep_agent(
        model=model_set.model,  # 使用配置的DeepSeek模型
        memory=list(MEMORY_FILES),  # 系统提示词文件（真实磁盘 prompt/AGENTS.md）
        backend=FilesystemBackend(
            root_dir=_PROJECT_ROOT, virtual_mode=True
        ),  # 真实磁盘后端，锚定项目根目录
        skills=[SKILLS_PATH],  # 技能路径（真实磁盘 skills/）
        tools=[*project_tools, *mcp_tools],  # 项目工具 + MCP 工具
        checkpointer=InMemorySaver(),  # 内存检查点保存
    )
    return agent
