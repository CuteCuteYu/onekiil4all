"""
========================================
Tools GraphRAG - 情报画板查询工具
========================================
功能: 基于当前情报分析图谱画板（CANVAS/GraphRAG Viz）的检索能力
- graphrag_status: 检查当前画板是否已保存（已保存才可接入 GraphRAG）
- graphrag_query:  按关键词检索画板实体，返回实体描述/属性/关联关系
 作者: 上古必斩必杀
"""

from langchain_core.tools import tool

from web.intelligence import graph_board
from web.intelligence.graph_board import GraphBoardError


@tool
def graphrag_status() -> str:
    """
    检查当前情报画板（GraphRAG）接入状态：画板名、是否已保存、节点/关系数。
    仅「已保存」时 GraphRAG 可用。用户问及画板/图谱时先调用本工具确认。
    """
    try:
        st = graph_board.graph_status()
        if not st["has_board"]:
            return (
                "当前未打开任何画板，GraphRAG 未接入。"
                "请提示用户在右侧 CANVAS 标签选择或创建画板并保存。"
            )
        state = (
            "已保存（GraphRAG 已接入）" if st["saved"] else "未保存（GraphRAG 未接入）"
        )
        return (
            f"画板：{st['board']}；保存状态：{state}；"
            f"节点 {st['nodes']} 个，关系 {st['edges']} 条"
        )
    except Exception as e:  # noqa: BLE001 - 工具约定：失败以错误字符串返回
        return f"[Error] 获取画板状态失败: {e}"


@tool
def graphrag_query(keyword: str) -> str:
    """
    查询当前情报画板（GraphRAG 检索）：按关键词匹配实体（名称/类型/描述/属性/来源），
    返回实体详情、关联关系与文本溯源。仅画板「已保存」时可查询，否则返回未接入提示。
    参数 keyword: 实体关键词，如 "APT29"、"恶意软件"、"update-cdn.net"。
    """
    try:
        if not graph_board.is_board_saved():
            return (
                "[Error] 当前画板尚未保存，GraphRAG 未接入。"
                "请直接告知用户先在画板（CANVAS 标签）点击「保存到本地」，"
                "保存成功后再查询；不要重复调用本工具。"
            )
        return graph_board.search_graph(keyword)
    except GraphBoardError as e:
        return f"[Error] {e.message}"
    except Exception as e:  # noqa: BLE001 - 工具约定：失败以错误字符串返回
        return f"[Error] GraphRAG 查询失败: {e}"
