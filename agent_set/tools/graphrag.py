"""
========================================
Tools GraphRAG - 情报画板查询工具
========================================
功能: 基于当前情报分析图谱画板（CANVAS/GraphRAG Viz）的检索与写入能力
- graphrag_status:  检查当前画板是否已保存（已保存才可接入 GraphRAG）
- graphrag_query:   按关键词检索画板实体，返回实体描述/属性/关联关系
- graph_add_node:   把分析结果实体写入画板（白名单类型）
- graph_add_edge:   把实体关系写入画板
 作者: 上古必斩必杀
"""

# 标准库
import re

# 第三方
from langchain_core.tools import tool

# 项目内部
from web.intelligence import graph_board
from web.intelligence.graph_board import GraphBoardError

# 实体 ID 合法字符（字母/数字/下划线/连字符），防止注入奇怪 ID 破坏画板数据
_ID_RE = re.compile(r"^[A-Za-z0-9_\-]+$")

# 入图操作允许的实体类型（开放给 Agent 写入的白名单）
_WRITABLE_TYPES = frozenset(
    {
        "FraudPattern",
        "PsychLever",
        "ScriptStage",
        "Persona",
        "ThreatActor",
        "Malware",
        "Tool",
        "Domain",
        "IP",
        "Vulnerability",
        "Organization",
        "Email",
        "Hash",
        "URL",
    }
)


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


@tool
def graph_add_node(
    node_id: str,
    name: str,
    node_type: str,
    description: str = "",
    properties: dict | None = None,
) -> str:
    """
    向当前情报画板添加（或更新）一个实体节点，用于把分析结果沉淀为知识图谱。
    画板打开即可写入（无需已保存）；写入后画板变为未保存状态属正常现象，
    可继续批量写入，全部写完后提醒用户在 CANVAS 点击「保存到本地」。
    参数 node_id: 实体唯一 ID，英文/数字/下划线/连字符，如 "fraud_gongjianfa"
    参数 name: 实体显示名称（必填），如 "冒充公检法诈骗"
    参数 node_type: 实体类型，白名单内取值：
        FraudPattern(骗术模式) / PsychLever(心理杠杆) / ScriptStage(话术阶段) /
        Persona(冒充角色原型) / ThreatActor / Malware / Tool / Domain / IP /
        Vulnerability / Organization / Email / Hash / URL
    参数 description: 自然语言描述（用于 GraphRAG 检索）
    参数 properties: 可选结构化元数据（如 {"intensity": "高", "evidence": "原文引用"}）
    """
    try:
        if not name or not name.strip():
            return "[Error] name 为必填参数，请提供实体显示名称（如 '冒充公检法诈骗'）"
        if not _ID_RE.match(node_id or ""):
            return (
                "[Error] node_id 只能包含字母/数字/下划线/连字符，如 fraud_gongjianfa"
            )
        if node_type not in _WRITABLE_TYPES:
            return (
                f"[Error] 不允许的实体类型: {node_type}。"
                f"可用类型: {', '.join(sorted(_WRITABLE_TYPES))}"
            )
        st = graph_board.graph_status()
        if not st["has_board"]:
            return (
                "[Error] 当前未打开任何画板。"
                "请提示用户在右侧 CANVAS 标签选择或创建画板并保存。"
            )
        node = {
            "id": node_id.strip(),
            "name": name.strip(),
            "type": node_type,
            "description": description or "",
            "properties": properties or {},
            "source_chunks": [],
        }
        result = graph_board.upsert_node(node)
        return (
            f"[OK] 实体已{'更新' if result['status'] == 'updated' else '写入'}画板: "
            f"{node_id} ({name})；可继续批量写入，"
            f"全部完成后提醒用户在 CANVAS 点击保存。"
        )
    except GraphBoardError as e:
        return f"[Error] {e.message}"
    except Exception as e:  # noqa: BLE001 - 工具约定：失败以错误字符串返回
        return f"[Error] 写入实体失败: {e}"


@tool
def graph_add_edge(
    edge_id: str,
    source: str,
    target: str,
    relation: str,
    description: str = "",
    weight: float = 0.5,
) -> str:
    """
    向当前情报画板添加（或更新）一条关系边。两端节点必须已存在（可先用 graph_add_node 创建）。
    画板打开即可写入（无需已保存）；可继续批量写入，全部写完后提醒用户保存。
    常用关系：USES（骗术模式→心理杠杆）、STAGE（骗术模式→话术阶段）、
    PERSONA（骗术模式→冒充角色原型）、CONTROLS / USES / TARGETS 等。
    参数 edge_id: 关系唯一 ID，英文/数字/下划线/连字符，如 "edge_gongjianfa_fear"
    参数 source: 源节点 ID
    参数 target: 目标节点 ID
    参数 relation: 关系动词，大写下划线，如 USES
    参数 description: 关系语义描述
    参数 weight: 置信度/强度 0.0~1.0
    """
    try:
        if not _ID_RE.match(edge_id or ""):
            return "[Error] edge_id 只能包含字母/数字/下划线/连字符"
        if not relation or not re.match(r"^[A-Z][A-Z0-9_]*$", relation):
            return "[Error] relation 必须是大写下划线形式，如 USES / STAGE / PERSONA"
        weight = max(0.0, min(1.0, float(weight)))
        st = graph_board.graph_status()
        if not st["has_board"]:
            return "[Error] 当前未打开任何画板。请提示用户先在 CANVAS 选择或创建画板。"
        edge = {
            "id": edge_id.strip(),
            "source": source.strip(),
            "target": target.strip(),
            "relation": relation,
            "description": description or "",
            "weight": weight,
        }
        result = graph_board.upsert_edge(edge)
        return (
            f"[OK] 关系已{'更新' if result['status'] == 'updated' else '写入'}画板: "
            f"{source} -[{relation}]-> {target}；"
            f"可继续批量写入，全部完成后提醒用户在 CANVAS 点击保存。"
        )
    except GraphBoardError as e:
        return f"[Error] {e.message}"
    except Exception as e:  # noqa: BLE001 - 工具约定：失败以错误字符串返回
        return f"[Error] 写入关系失败: {e}"
