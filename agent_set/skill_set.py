"""
========================================
Skill Set - 技能集模块
========================================
功能: 加载和管理AI Agent的技能
从~/.claude/skills目录读取技能定义文件
 作者: CuteCuteYu
"""

# ═══════════════════════════════════════════════════════════════
# 导入标准库
# ═══════════════════════════════════════════════════════════════

from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# 导入DeepAgents工具函数
# ═══════════════════════════════════════════════════════════════

from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore


# ═══════════════════════════════════════════════════════════════
# 技能加载函数
# ═══════════════════════════════════════════════════════════════


def load_skill() -> dict:
    """
    加载所有可用技能

    从~/.claude/skills目录读取每个技能的SKILL.md文件

    返回:
        技能字典，键为技能名称，值为技能内容文本
    """
    # 技能目录路径
    skills_dir = Path.home() / ".claude" / "skills"
    skills_dict = {}

    # 遍历技能目录
    for folder in skills_dir.iterdir() if skills_dir.exists() else []:
        if folder.is_dir():
            skill_md = folder / "SKILL.md"
            if skill_md.exists():
                try:
                    # 读取技能文件内容
                    skills_dict[folder.name] = skill_md.read_text(encoding="utf-8")
                except Exception as e:
                    skills_dict[folder.name] = f"Error: {e}"
    return skills_dict


# ═══════════════════════════════════════════════════════════════
# 技能存储创建函数
# ═══════════════════════════════════════════════════════════════


def create_skill_store():
    """
    创建技能存储实例

    将加载的技能存入内存存储，供Agent使用

    返回:
        InMemoryStore实例，包含所有技能
    """
    # 创建内存存储
    store = InMemoryStore()

    # 加载所有技能
    skills_dict = load_skill()

    # 将每个技能存入存储
    for skill_name, skill_content in skills_dict.items():
        store.put(
            namespace=("filesystem",),
            key=f"/skills/{skill_name}/SKILL.md",
            value=create_file_data(skill_content),
        )
    return store
