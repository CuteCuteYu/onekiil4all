"""
========================================
Agent Set - Agent配置模块
========================================
功能: 创建和配置AI Agent
整合模型、工具、技能和记忆系统
作者: onekiil4all
"""

# ═══════════════════════════════════════════════════════════════
# 导入DeepAgents框架和LangChain组件
# ═══════════════════════════════════════════════════════════════

from deepagents import create_deep_agent
from deepagents.backends import StoreBackend
from langgraph.checkpoint.memory import InMemorySaver

# ═══════════════════════════════════════════════════════════════
# 导入项目内部模块
# ═══════════════════════════════════════════════════════════════

from .skill_set import create_skill_store  # 技能存储创建
from .tools_set import tools  # 工具列表
from model_set import model_set  # 模型配置


# ═══════════════════════════════════════════════════════════════
# 初始化技能存储
# ═══════════════════════════════════════════════════════════════

# 创建技能存储实例
store = create_skill_store()


# ═══════════════════════════════════════════════════════════════
# Agent创建函数
# ═══════════════════════════════════════════════════════════════


def create_agent():
    """
    创建配置好的Agent实例

    整合以下组件：
    - AI模型 (DeepSeek)
    - 工具集 (tools_set中定义的工具)
    - 技能集 (从~/.claude/skills目录加载)
    - 记忆系统 (InMemorySaver用于检查点)
    - 系统提示词 (AGENTS.md)

    返回:
        配置好的Agent实例
    """
    agent = create_deep_agent(
        model=model_set.model,  # 使用配置的DeepSeek模型
        memory=["./prompt/AGENTS.md"],  # 系统提示词文件
        backend=(lambda rt: StoreBackend(rt)),  # 存储后端
        store=store,  # 技能存储
        skills=["/skills/"],  # 技能路径
        tools=tools,  # 可用工具列表
        checkpointer=InMemorySaver(),  # 内存检查点保存
    )
    return agent
