"""
========================================
Graph Board - 情报分析图谱画板模块
========================================
功能: 本地知识图谱可视化 + GraphRAG 数据准备
- 画板以独立文件管理（data/graphs/*.json）：可创建全新空画板，也可打开已有画板继续编辑
- 当前画板载入内存，变动时按需保存（原子写回）
- 数据目录与告警/RSS 一致放在 data/（运行时数据，gitignored）
 作者: 上古必斩必杀
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
from datetime import UTC, datetime
from pathlib import Path

import networkx as nx

logger = logging.getLogger(__name__)

# 项目根目录（web/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 旧版单文件（启动时迁移为默认画板）
DATA_FILE = BASE_DIR / "data" / "graph_data.json"

# 画板目录：每个画板一个独立 JSON 文件
BOARDS_DIR = BASE_DIR / "data" / "graphs"

# 内存中的图数据（当前画板）
graph_data: dict = {"types": {}, "nodes": [], "edges": []}
current_board: str = ""  # 当前画板名（不含扩展名）
_lock = threading.Lock()

# 内置默认实体类型（graph_data.json 缺少 types 字段时使用）
DEFAULT_TYPES: dict = {
    "ThreatActor": {
        "label": "威胁组织",
        "color": "#f43f5e",
        "shape": "star",
        "builtin": True,
    },
    "Malware": {
        "label": "恶意软件",
        "color": "#a855f7",
        "shape": "diamond",
        "builtin": True,
    },
    "Tool": {"label": "工具", "color": "#f97316", "shape": "hexagon", "builtin": True},
    "Domain": {
        "label": "域名",
        "color": "#22d3ee",
        "shape": "round-rectangle",
        "builtin": True,
    },
    "IP": {"label": "IP 地址", "color": "#3b82f6", "shape": "ellipse", "builtin": True},
    "Vulnerability": {
        "label": "漏洞",
        "color": "#facc15",
        "shape": "triangle",
        "builtin": True,
    },
    "Organization": {
        "label": "组织",
        "color": "#10b981",
        "shape": "octagon",
        "builtin": True,
    },
    "Email": {
        "label": "邮件",
        "color": "#ec4899",
        "shape": "round-tag",
        "builtin": True,
    },
    "Hash": {"label": "哈希", "color": "#94a3b8", "shape": "pentagon", "builtin": True},
    "URL": {
        "label": "URL",
        "color": "#2dd4bf",
        "shape": "round-hexagon",
        "builtin": True,
    },
}


class GraphBoardError(Exception):
    """画板操作错误：携带 HTTP 状态码，由 API 层转换为 HTTPException。"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_boards() -> None:
    """确保画板目录存在，并将旧版 graph_data.json 迁移为默认画板。"""
    BOARDS_DIR.mkdir(parents=True, exist_ok=True)
    if not any(BOARDS_DIR.glob("*.json")) and DATA_FILE.exists():
        shutil.copy(DATA_FILE, BOARDS_DIR / "默认画板.json")


def list_boards() -> list[dict]:
    """扫描画板目录，返回画板元信息列表。"""
    boards = []
    for f in sorted(BOARDS_DIR.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            boards.append(
                {
                    "name": f.stem,
                    "nodes": len(data.get("nodes", [])),
                    "edges": len(data.get("edges", [])),
                    "updated_at": datetime.fromtimestamp(f.stat().st_mtime, tz=UTC)
                    .astimezone()
                    .strftime("%Y-%m-%d %H:%M"),
                }
            )
        except Exception as exc:  # noqa: BLE001 - 单文件损坏不影响其余画板
            logger.warning("跳过无法解析的画板文件 %s: %s", f.name, exc)
            continue
    return boards


def load_board(name: str) -> None:
    """载入指定画板到内存。"""
    global graph_data, current_board
    path = BOARDS_DIR / f"{name}.json"
    if not path.exists():
        raise GraphBoardError(f"画板不存在: {name}", 404)
    with open(path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    # 兼容旧数据：缺少 types 字段时补默认类型
    if "types" not in graph_data:
        graph_data["types"] = dict(DEFAULT_TYPES)
    current_board = name


def save_board() -> None:
    """将内存图数据原子写回当前画板文件（临时文件 + rename）。"""
    if not current_board:
        raise GraphBoardError("未打开任何画板", 400)
    path = BOARDS_DIR / f"{current_board}.json"
    tmp_file = path.with_suffix(".json.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, path)


def build_nx() -> nx.DiGraph:
    """基于内存数据构建 NetworkX 有向图，节点/边属性随图携带。"""
    G = nx.DiGraph()
    for n in graph_data["nodes"]:
        G.add_node(n["id"], **n)
    for e in graph_data["edges"]:
        G.add_edge(e["source"], e["target"], **e)
    return G


def validate_board_name(name: str) -> str:
    """校验并返回规范化画板名。"""
    name = name.strip()
    if not name:
        raise GraphBoardError("画板名不能为空", 400)
    if any(c in name for c in '\\/:*?"<>|'):
        raise GraphBoardError('画板名包含非法字符 \\ / : * ? " < > |', 400)
    return name


# ---------------------------------------------------------------------------
# 画板管理
# ---------------------------------------------------------------------------
def get_boards() -> dict:
    """列出所有画板及当前打开的画板。"""
    with _lock:
        return {"boards": list_boards(), "current": current_board}


def create_board(name: str) -> dict:
    """创建全新的空画板。"""
    with _lock:
        name = validate_board_name(name)
        path = BOARDS_DIR / f"{name}.json"
        if path.exists():
            raise GraphBoardError(f"画板已存在: {name}", 400)
        data = {"types": dict(DEFAULT_TYPES), "nodes": [], "edges": []}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "created", "name": name}


def open_board(name: str) -> dict:
    """打开指定画板并载入内存，返回画板数据。"""
    with _lock:
        load_board(name)
        return {"status": "opened", "name": current_board, "graph": graph_data}


def rename_board(old_name: str, new_name: str) -> dict:
    """重命名画板。"""
    with _lock:
        old_name = old_name.strip()
        new_name = validate_board_name(new_name)
        old_path = BOARDS_DIR / f"{old_name}.json"
        new_path = BOARDS_DIR / f"{new_name}.json"
        if not old_path.exists():
            raise GraphBoardError(f"画板不存在: {old_name}", 404)
        if new_path.exists():
            raise GraphBoardError(f"画板已存在: {new_name}", 400)
        old_path.rename(new_path)
        global current_board
        if current_board == old_name:
            current_board = new_name
        return {"status": "renamed", "name": new_name}


def delete_board(name: str) -> dict:
    """删除画板文件；若删除的是当前画板，则切换到第一个可用画板。"""
    with _lock:
        global graph_data, current_board
        path = BOARDS_DIR / f"{name}.json"
        if not path.exists():
            raise GraphBoardError(f"画板不存在: {name}", 404)
        path.unlink()
        if current_board == name:
            boards = list_boards()
            if boards:
                load_board(boards[0]["name"])
            else:
                graph_data = {"types": dict(DEFAULT_TYPES), "nodes": [], "edges": []}
                current_board = ""
        return {"status": "deleted", "name": name}


# ---------------------------------------------------------------------------
# 图数据
# ---------------------------------------------------------------------------
def get_graph() -> dict:
    """读取内存中的全局图数据。"""
    with _lock:
        return graph_data


def _serialize(data: dict) -> str:
    """将图数据归一化序列化（排序键），用于一致性比较 / 快速检索。"""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)


def is_board_saved() -> bool:
    """检查当前画板内存数据是否与磁盘文件一致（无未保存修改）。"""
    if not current_board:
        return False
    path = BOARDS_DIR / f"{current_board}.json"
    if not path.exists():
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
    except Exception as exc:  # noqa: BLE001 - 文件损坏视为未保存
        logger.warning("读取画板文件失败 %s: %s", path, exc)
        return False
    with _lock:
        return _serialize(graph_data) == _serialize(on_disk)


def graph_status() -> dict:
    """当前画板状态：是否已打开、是否已保存、节点/边数量。"""
    with _lock:
        board = current_board
        has_board = bool(board)
        nodes = len(graph_data.get("nodes", []))
        edges = len(graph_data.get("edges", []))
    return {
        "board": board,
        "has_board": has_board,
        "saved": is_board_saved(),
        "nodes": nodes,
        "edges": edges,
    }


def search_graph(keyword: str, limit: int = 5, max_chars: int = 6000) -> str:
    """
    在当前画板中按关键词检索实体（GraphRAG 查询），返回实体详情/描述/关联关系文本。

    匹配范围：节点 名称 / 类型 / 描述 / 结构化属性 / 来源片段。
    参数:
        keyword: 检索关键词
        limit: 最多返回的实体数（>=1）
        max_chars: 返回文本最大长度，超出部分截断（控制 Agent 上下文占用）

    关键词为空或未打开画板时抛出 GraphBoardError。
    """
    if not keyword or not keyword.strip():
        raise GraphBoardError("检索关键词不能为空", 400)
    limit = max(limit, 1)
    with _lock:
        if not current_board:
            raise GraphBoardError("未打开任何画板", 400)
        kw = keyword.strip()
        kw_lower = kw.lower()

        index: list[tuple[dict, str]] = []
        for n in graph_data["nodes"]:
            haystack = " ".join(
                [
                    str(n.get("name", "")),
                    str(n.get("type", "")),
                    str(n.get("description", "")),
                    json.dumps(
                        n.get("properties", {}), ensure_ascii=False, default=str
                    ),
                    " ".join(str(c) for c in n.get("source_chunks", [])),
                ]
            ).lower()
            index.append((n, haystack))

        # 名称/类型命中优先于描述/属性/来源命中，提升检索精准度
        scored = []
        for n, haystack in index:
            if kw_lower in haystack:
                score = 0
                if kw_lower in str(n.get("name", "")).lower():
                    score += 100
                if kw_lower in str(n.get("type", "")).lower():
                    score += 50
                if kw_lower in str(n.get("description", "")).lower():
                    score += 10
                scored.append((score, n))
        scored.sort(key=lambda item: item[0], reverse=True)
        matched = [n for _, n in scored]
        if not matched:
            return (
                f"当前画板「{current_board}」中未找到与关键词「{keyword}」"
                f"相关的实体（共 {len(graph_data['nodes'])} 个节点）。"
            )

        G = build_nx()
        lines = [
            f"# GraphRAG 查询结果：{keyword}（画板：{current_board}）",
            f"找到 {len(matched)} 个相关实体：",
        ]
        for n in matched[:limit]:
            lines.append("")
            lines.append(f"## {n.get('name')}（{n.get('type')}）")
            if n.get("description"):
                lines.append(f"描述：{n['description']}")
            for k, v in (n.get("properties") or {}).items():
                lines.append(f"{k}: {v}")
            rels = []
            for u, v, d in G.edges(data=True):
                if u == n["id"] or v == n["id"]:
                    other_id = v if u == n["id"] else u
                    other = G.nodes[other_id].get("name", other_id)
                    rels.append(
                        f"{n['name']} --[{d.get('relation', 'RELATED_TO')}]--> "
                        f"{other} (weight={d.get('weight', 0.5)})"
                    )
            if rels:
                lines.append("关联关系：" + "；".join(rels))
            for c in (n.get("source_chunks") or [])[:3]:
                lines.append(f"溯源：{c}")
        result = "\n".join(lines)
        if len(result) > max_chars:
            result = result[:max_chars].rstrip() + "\n...（结果过长已截断）"
        return result


# ---------------------------------------------------------------------------
# 实体类型管理（支持用户自定义实体类型）
# ---------------------------------------------------------------------------
def get_types() -> dict:
    """获取全部实体类型定义（内置 + 自定义）。"""
    with _lock:
        return graph_data.get("types", DEFAULT_TYPES)


def upsert_type(
    name: str, label: str = "", color: str = "#64748b", shape: str = "ellipse"
) -> dict:
    """新增或更新自定义实体类型（名称/标签/颜色/形状）。"""
    with _lock:
        name = name.strip()
        if not name:
            raise GraphBoardError("类型名不能为空", 400)
        types = graph_data.setdefault("types", dict(DEFAULT_TYPES))
        existed = name in types
        types[name] = {
            "label": label or name,
            "color": color,
            "shape": shape,
            "builtin": types.get(name, {}).get("builtin", False),
        }
        return {"status": "updated" if existed else "created", "type": types[name]}


def delete_type(type_name: str) -> dict:
    """删除自定义实体类型（内置类型不可删除）。"""
    with _lock:
        types = graph_data.get("types", {})
        if type_name not in types:
            raise GraphBoardError(f"类型不存在: {type_name}", 404)
        if types[type_name].get("builtin"):
            raise GraphBoardError("内置类型不可删除", 400)
        used = [n["id"] for n in graph_data["nodes"] if n.get("type") == type_name]
        if used:
            raise GraphBoardError(
                f"仍有 {len(used)} 个节点使用该类型，请先修改或删除这些节点", 400
            )
        del types[type_name]
        return {"status": "deleted", "type_name": type_name}


# ---------------------------------------------------------------------------
# 1 跳展开
# ---------------------------------------------------------------------------
def expand_node(node_id: str) -> dict:
    """利用 NetworkX 检索指定节点的 1 跳关联邻居与边，返回子图。"""
    with _lock:
        G = build_nx()
        if node_id not in G:
            raise GraphBoardError(f"节点不存在: {node_id}", 404)

        neighbors = set(G.neighbors(node_id)) | set(G.predecessors(node_id))
        sub_nodes = [dict(G.nodes[n]) for n in neighbors]
        sub_edges = [
            dict(G.edges[u, v])
            for u, v in G.edges
            if u == node_id or v == node_id or (u in neighbors and v in neighbors)
        ]
        return {"nodes": sub_nodes, "edges": sub_edges}


# ---------------------------------------------------------------------------
# 节点增删改
# ---------------------------------------------------------------------------
def upsert_node(node: dict) -> dict:
    """新增或更新节点信息（含 description 描述字段）。"""
    with _lock:
        for i, n in enumerate(graph_data["nodes"]):
            if n["id"] == node["id"]:
                graph_data["nodes"][i] = node
                return {"status": "updated", "node": graph_data["nodes"][i]}
        graph_data["nodes"].append(node)
        return {"status": "created", "node": node}


def delete_node(node_id: str) -> dict:
    """从内存中移除节点，并级联删除所有关联边。"""
    with _lock:
        before = len(graph_data["nodes"])
        graph_data["nodes"] = [n for n in graph_data["nodes"] if n["id"] != node_id]
        removed_edges = [
            e
            for e in graph_data["edges"]
            if e["source"] == node_id or e["target"] == node_id
        ]
        graph_data["edges"] = [
            e
            for e in graph_data["edges"]
            if e["source"] != node_id and e["target"] != node_id
        ]
        if len(graph_data["nodes"]) == before:
            raise GraphBoardError(f"节点不存在: {node_id}", 404)
        return {
            "status": "deleted",
            "node_id": node_id,
            "removed_edges": len(removed_edges),
        }


# ---------------------------------------------------------------------------
# 关系增改
# ---------------------------------------------------------------------------
def upsert_edge(edge: dict) -> dict:
    """新增或更新关系。"""
    with _lock:
        G = build_nx()
        if edge["source"] not in G:
            raise GraphBoardError(f"源节点不存在: {edge['source']}", 404)
        if edge["target"] not in G:
            raise GraphBoardError(f"目标节点不存在: {edge['target']}", 404)

        for i, e in enumerate(graph_data["edges"]):
            if e["id"] == edge["id"]:
                graph_data["edges"][i] = edge
                return {"status": "updated", "edge": graph_data["edges"][i]}
        graph_data["edges"].append(edge)
        return {"status": "created", "edge": edge}


# ---------------------------------------------------------------------------
# 持久化保存
# ---------------------------------------------------------------------------
def save() -> dict:
    """将当前内存图数据全量持久化写回当前画板文件。"""
    with _lock:
        save_board()
        return {
            "status": "saved",
            "board": current_board,
            "nodes": len(graph_data["nodes"]),
            "edges": len(graph_data["edges"]),
            "file": str(BOARDS_DIR / f"{current_board}.json"),
        }


# ---------------------------------------------------------------------------
# GraphRAG 检索上下文（1~2 跳子图 → Prompt Context）
# ---------------------------------------------------------------------------
def rag_context(node_id: str) -> dict:
    """
    根据指定节点 ID，提取其 1~2 跳的子图语义三元组与实体描述，
    拼接并返回一段完整的检索上下文文本（Prompt Context）。
    """
    with _lock:
        G = build_nx()
        if node_id not in G:
            raise GraphBoardError(f"节点不存在: {node_id}", 404)

        # BFS 收集 1~2 跳节点
        hop1 = set(G.neighbors(node_id)) | set(G.predecessors(node_id))
        hop2: set = set()
        for n in hop1:
            hop2 |= set(G.neighbors(n)) | set(G.predecessors(n))
        hop2 -= {node_id}
        hop2 -= hop1

        focus = G.nodes[node_id]
        lines: list[str] = []
        lines.append(f"# 检索上下文：{focus.get('name', node_id)}")
        lines.append("## 实体描述（Entity Description）")
        lines.append(
            f"- {focus.get('name', node_id)}（{focus.get('type', 'Unknown')}）：{focus.get('description', '')}"
        )

        def _render_triplets(edges: list, label: str) -> None:
            if not edges:
                return
            lines.append(f"## {label}（语义三元组）")
            for u, v, data in edges:
                src = G.nodes[u].get("name", u)
                dst = G.nodes[v].get("name", v)
                rel = data.get("relation", "RELATED_TO")
                desc = data.get("description", "")
                w = data.get("weight", 0.5)
                lines.append(f"- ({src}) --[{rel} (weight={w})]--> ({dst})：{desc}")

        # 1 跳关系：焦点节点与其 1 跳邻居之间的边（两端均在 {node_id} ∪ hop1）
        focus_set = hop1 | {node_id}
        hop1_edges = [
            (u, v, d)
            for u, v, d in G.edges(data=True)
            if u in focus_set and v in focus_set
        ]
        hop1_keys = {(u, v) for u, v, _ in hop1_edges}
        # 2 跳关系：连接 2 跳节点的边（排除已在 1 跳展示的边）
        hop2_edges = [
            (u, v, d)
            for u, v, d in G.edges(data=True)
            if (u in hop2 or v in hop2) and (u, v) not in hop1_keys
        ]

        _render_triplets(hop1_edges, "1 跳关系")
        _render_triplets(hop2_edges, "2 跳关系")

        # 关联文本溯源
        chunks = focus.get("source_chunks", [])
        if chunks:
            lines.append("## 关联文本溯源（Source Chunks）")
            for c in chunks:
                lines.append(f"- {c}")

        return {"node_id": node_id, "context": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 初始化：确保画板目录并打开第一个画板（或创建默认空画板）
# ---------------------------------------------------------------------------
ensure_boards()
_boards = list_boards()
if _boards:
    load_board(_boards[0]["name"])
else:
    graph_data = {"types": dict(DEFAULT_TYPES), "nodes": [], "edges": []}
    current_board = "默认画板"
    save_board()
