"""
========================================
Skill Set - 技能集模块
========================================
功能: 加载和管理AI Agent的技能
从项目内 skills/ 目录读取技能定义文件
（默认不读取 Claude Code 的 ~/.claude/skills，可用 SKILLS_DIR 覆盖）
 作者: CuteCuteYu
"""

# ══════════════════════════════════════════════════════════════
# 导入标准库
# ══════════════════════════════════════════════════════════════

import os
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# 导入DeepAgents工具函数
# ══════════════════════════════════════════════════════════════
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

# ══════════════════════════════════════════════════════════════
# 技能目录配置（项目内，独立于任何外部工具的全局目录）
# ══════════════════════════════════════════════════════════════

# 项目根目录（agent_set/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 技能目录：默认使用项目内的 skills/，可用环境变量 SKILLS_DIR 覆盖
SKILLS_DIR = Path(os.environ.get("SKILLS_DIR") or (_PROJECT_ROOT / "skills"))

# ═══════════════════════════════════════════════════════════════
# 技能加载函数
# ═══════════════════════════════════════════════════════════════


def load_skill() -> dict:
    """
    加载所有可用技能

    从项目内技能目录（SKILLS_DIR，默认 skills/）读取每个技能的 SKILL.md 文件。

    返回:
        技能字典，键为技能名称，值为技能内容文本
    """
    skills_dict = {}

    # 遍历技能目录
    for folder in SKILLS_DIR.iterdir() if SKILLS_DIR.exists() else []:
        if folder.is_dir():
            skill_md = folder / "SKILL.md"
            if skill_md.exists():
                try:
                    # 读取技能文件内容
                    skills_dict[folder.name] = skill_md.read_text(encoding="utf-8")
                except OSError as e:
                    skills_dict[folder.name] = f"Error: {e}"
    return skills_dict


def load_skill_files() -> dict[str, dict[str, str]]:
    """
    加载所有技能及其辅助文件

    从项目内技能目录（SKILLS_DIR，默认 skills/）读取。

    返回:
        {技能名: {相对路径: 文件内容}}，包含 SKILL.md 和 references/ 等辅助文件
    """
    result: dict[str, dict[str, str]] = {}

    for folder in SKILLS_DIR.iterdir() if SKILLS_DIR.exists() else []:
        if not folder.is_dir():
            continue
        files: dict[str, str] = {}
        # 递归收集技能目录下所有文本文件（限制深度避免过大）
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(folder).as_posix()
            # 跳过二进制/大文件，只加载常见文本文件
            if path.stat().st_size > 200_000:
                continue
            if path.suffix.lower() in {".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml", ".toml", ".js", ".ts"}:
                try:
                    files[rel] = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
        if files:
            result[folder.name] = files
    return result


# ═══════════════════════════════════════════════════════════════
# 技能存储创建函数
# ═══════════════════════════════════════════════════════════════

# 说明：Agent 现在使用 FilesystemBackend 从真实磁盘直接读取 skills/
# （见 agent_set/agent_set.py），因此 create_skill_store() 不再是必需路径，
# 仅保留给「把技能预置进 StoreBackend / StateBackend」这类用法。


def create_skill_store():
    """
    创建技能存储实例

    将加载的技能（含 SKILL.md 与 references/ 等辅助文件）存入内存存储，
    供Agent使用

    返回:
        InMemoryStore实例，包含所有技能
    """
    # 创建内存存储
    store = InMemoryStore()

    # 加载所有技能及其辅助文件
    skills_files = load_skill_files()

    # 将每个技能文件存入存储
    for skill_name, files in skills_files.items():
        for rel_path, content in files.items():
            store.put(
                namespace=("filesystem",),
                key=f"/skills/{skill_name}/{rel_path}",
                value=create_file_data(content),
            )
    return store
