"""
========================================
Meta API - 技能与工具路由
========================================
功能: 列出Agent可用的技能和工具
 作者: CuteCuteYu
"""

from fastapi import APIRouter

from agent_set.skill_set import load_skill
from agent_set.tools_set import tools

router = APIRouter()


def _extract_description(content: str, fallback: str) -> str:
    """
    从 SKILL.md 内容提取描述

    跳过 YAML frontmatter（--- ... ---），取其后第一个非空行并去掉 Markdown 标题符号

    参数:
        content: SKILL.md 文本
        fallback: 提取失败时的回退值

    返回:
        描述字符串
    """
    lines = content.split("\n")

    # 跳过 YAML frontmatter（未闭合时视为无效内容）
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1 :]
                break
        else:
            return fallback

    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("#").strip()
    return fallback


@router.get("/api/skills")
async def api_list_skills():
    """
    列出可用的技能列表

    复用 skill_set.load_skill() 读取 ~/.claude/skills 目录

    返回:
        技能列表，每个技能包含id和description
    """
    skills = [
        {
            "id": skill_name,
            "description": _extract_description(skill_content, skill_name),
        }
        for skill_name, skill_content in load_skill().items()
    ]

    # 按技能ID排序返回
    return {"skills": sorted(skills, key=lambda x: x["id"])}


@router.get("/api/tools")
async def api_list_tools():
    """
    列出可用的工具列表

    返回:
        工具列表，每个工具包含name和description
    """
    return {
        "tools": [
            {"name": tool.name, "description": tool.description.strip()}
            for tool in tools
        ]
    }
