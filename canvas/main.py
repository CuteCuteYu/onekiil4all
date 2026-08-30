"""
GraphRAG Viz — 本地知识图谱可视化 + GraphRAG 数据准备服务
============================================================
- FastAPI + NetworkX 后端
- 画板以独立文件管理（graphs/*.json）：可创建全新空画板，也可打开已有画板继续编辑
- 当前画板载入内存，变动时按需保存
- 静态托管 static/ 目录下的单文件前端
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
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 路径与全局状态
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "graph_data.json"   # 旧版单文件（启动时迁移为默认画板）
BOARDS_DIR = BASE_DIR / "graphs"           # 画板目录：每个画板一个独立 JSON 文件
STATIC_DIR = BASE_DIR / "static"

# 确保静态目录存在（避免 StaticFiles 挂载失败）
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 内存中的图数据（当前画板）
graph_data: dict = {"types": {}, "nodes": [], "edges": []}
current_board: str = ""   # 当前画板名（不含扩展名）
_lock = threading.Lock()

# 内置默认实体类型（graph_data.json 缺少 types 字段时使用）
DEFAULT_TYPES: dict = {
    "ThreatActor": {"label": "威胁组织", "color": "#f43f5e", "shape": "star", "builtin": True},
    "Malware": {"label": "恶意软件", "color": "#a855f7", "shape": "diamond", "builtin": True},
    "Tool": {"label": "工具", "color": "#f97316", "shape": "hexagon", "builtin": True},
    "Domain": {"label": "域名", "color": "#22d3ee", "shape": "round-rectangle", "builtin": True},
    "IP": {"label": "IP 地址", "color": "#3b82f6", "shape": "ellipse", "builtin": True},
    "Vulnerability": {"label": "漏洞", "color": "#facc15", "shape": "triangle", "builtin": True},
    "Organization": {"label": "组织", "color": "#10b981", "shape": "octagon", "builtin": True},
    "Email": {"label": "邮件", "color": "#ec4899", "shape": "round-tag", "builtin": True},
    "Hash": {"label": "哈希", "color": "#94a3b8", "shape": "pentagon", "builtin": True},
    "URL": {"label": "URL", "color": "#2dd4bf", "shape": "round-hexagon", "builtin": True},
}


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
            boards.append({
                "name": f.stem,
                "nodes": len(data.get("nodes", [])),
                "edges": len(data.get("edges", [])),
                "updated_at": datetime.fromtimestamp(
                    f.stat().st_mtime, tz=UTC
                ).astimezone().strftime("%Y-%m-%d %H:%M"),
            })
        except Exception as exc:  # noqa: BLE001 - 单文件损坏不影响其余画板
            logger.warning("跳过无法解析的画板文件 %s: %s", f.name, exc)
            continue
    return boards


def load_board(name: str) -> None:
    """载入指定画板到内存。"""
    global graph_data, current_board
    path = BOARDS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"画板不存在: {name}")
    with open(path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    # 兼容旧数据：缺少 types 字段时补默认类型
    if "types" not in graph_data:
        graph_data["types"] = dict(DEFAULT_TYPES)
    current_board = name


def save_board() -> None:
    """将内存图数据原子写回当前画板文件（临时文件 + rename）。"""
    if not current_board:
        raise HTTPException(status_code=400, detail="未打开任何画板")
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


# ---------------------------------------------------------------------------
# Pydantic 请求模型（严格遵循 GraphRAG 字段规范）
# ---------------------------------------------------------------------------
class NodeIn(BaseModel):
    id: str = Field(..., description="节点唯一标识，如 ent_baoyu")
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型，如 Character / Place / Concept")
    description: str = Field("", description="自然语言描述，用于 GraphRAG 生成 Entity Embedding")
    properties: dict = Field(default_factory=dict, description="结构化元数据")
    source_chunks: list = Field(default_factory=list, description="关联的原始文本片段 ID 或简述")


class EdgeIn(BaseModel):
    id: str = Field(..., description="关系唯一标识")
    source: str = Field(..., description="源节点 ID")
    target: str = Field(..., description="目标节点 ID")
    relation: str = Field(..., description="关系动词，大写下划线，如 LOVES / RESIDES_IN")
    description: str = Field("", description="关系的语义描述，用于 RAG 检索提供边上下文")
    weight: float = Field(0.5, ge=0.0, le=1.0, description="关系置信度或强度 0.0~1.0")


class TypeIn(BaseModel):
    name: str = Field(..., description="类型名（英文标识）")
    label: str = Field("", description="显示标签")
    color: str = Field("#64748b", description="节点颜色")
    shape: str = Field("ellipse", description="节点形状")


class BoardCreate(BaseModel):
    name: str = Field(..., description="新画板名称")


class BoardOpen(BaseModel):
    name: str = Field(..., description="要打开的画板名称")


class BoardRename(BaseModel):
    old_name: str = Field(..., description="原画板名称")
    new_name: str = Field(..., description="新画板名称")


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(
    title="GraphRAG Viz — 情报分析图谱",
    description="本地情报分析图谱可视化与 GraphRAG 数据准备服务：将收集的情报实体与关系可视化、下钻分析并导出为 GraphRAG 索引",
    version="1.0.0",
)

# 启动：确保画板目录并打开第一个画板（或创建默认空画板）
ensure_boards()
_boards = list_boards()
if _boards:
    load_board(_boards[0]["name"])
else:
    graph_data = {"types": dict(DEFAULT_TYPES), "nodes": [], "edges": []}
    current_board = "默认画板"
    save_board()


# ---------------------------------------------------------------------------
# API: 画板管理（独立文件管理）
# ---------------------------------------------------------------------------
@app.get("/api/boards")
def get_boards() -> dict:
    """列出所有画板及当前打开的画板。"""
    with _lock:
        return {"boards": list_boards(), "current": current_board}


@app.post("/api/boards")
def create_board(body: BoardCreate) -> dict:
    """创建全新的空画板。"""
    with _lock:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="画板名不能为空")
        if any(c in name for c in '\\/:*?"<>|'):
            raise HTTPException(status_code=400, detail="画板名包含非法字符 \\ / : * ? \" < > |")
        path = BOARDS_DIR / f"{name}.json"
        if path.exists():
            raise HTTPException(status_code=400, detail=f"画板已存在: {name}")
        data = {"types": dict(DEFAULT_TYPES), "nodes": [], "edges": []}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "created", "name": name}


@app.post("/api/boards/open")
def open_board(body: BoardOpen) -> dict:
    """打开指定画板并载入内存，返回画板数据。"""
    with _lock:
        load_board(body.name)
        return {"status": "opened", "name": current_board, "graph": graph_data}


@app.post("/api/boards/rename")
def rename_board(body: BoardRename) -> dict:
    """重命名画板。"""
    with _lock:
        old, new = body.old_name.strip(), body.new_name.strip()
        if not new:
            raise HTTPException(status_code=400, detail="新画板名不能为空")
        if any(c in new for c in '\\/:*?"<>|'):
            raise HTTPException(status_code=400, detail="画板名包含非法字符 \\ / : * ? \" < > |")
        old_path = BOARDS_DIR / f"{old}.json"
        new_path = BOARDS_DIR / f"{new}.json"
        if not old_path.exists():
            raise HTTPException(status_code=404, detail=f"画板不存在: {old}")
        if new_path.exists():
            raise HTTPException(status_code=400, detail=f"画板已存在: {new}")
        old_path.rename(new_path)
        global current_board
        if current_board == old:
            current_board = new
        return {"status": "renamed", "name": new}


@app.delete("/api/boards/{name}")
def delete_board(name: str) -> dict:
    """删除画板文件；若删除的是当前画板，则切换到第一个可用画板。"""
    with _lock:
        global graph_data, current_board
        path = BOARDS_DIR / f"{name}.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"画板不存在: {name}")
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
# API: 图数据
# ---------------------------------------------------------------------------
@app.get("/api/graph")
def get_graph() -> dict:
    """读取内存中的全局图数据。"""
    with _lock:
        return graph_data


# ---------------------------------------------------------------------------
# API: 实体类型管理（支持用户自定义实体类型）
# ---------------------------------------------------------------------------
@app.get("/api/types")
def get_types() -> dict:
    """获取全部实体类型定义（内置 + 自定义）。"""
    with _lock:
        return graph_data.get("types", DEFAULT_TYPES)


@app.post("/api/types")
def upsert_type(t: TypeIn) -> dict:
    """新增或更新自定义实体类型（名称/标签/颜色/形状）。"""
    with _lock:
        name = t.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="类型名不能为空")
        types = graph_data.setdefault("types", dict(DEFAULT_TYPES))
        existed = name in types
        types[name] = {
            "label": t.label or name,
            "color": t.color,
            "shape": t.shape,
            "builtin": types.get(name, {}).get("builtin", False),
        }
        return {"status": "updated" if existed else "created", "type": types[name]}


@app.delete("/api/types/{type_name}")
def delete_type(type_name: str) -> dict:
    """删除自定义实体类型（内置类型不可删除）。"""
    with _lock:
        types = graph_data.get("types", {})
        if type_name not in types:
            raise HTTPException(status_code=404, detail=f"类型不存在: {type_name}")
        if types[type_name].get("builtin"):
            raise HTTPException(status_code=400, detail="内置类型不可删除")
        used = [n["id"] for n in graph_data["nodes"] if n.get("type") == type_name]
        if used:
            raise HTTPException(
                status_code=400,
                detail=f"仍有 {len(used)} 个节点使用该类型，请先修改或删除这些节点",
            )
        del types[type_name]
        return {"status": "deleted", "type_name": type_name}


# ---------------------------------------------------------------------------
# API: 1 跳展开
# ---------------------------------------------------------------------------
@app.get("/api/expand/{node_id}")
def expand_node(node_id: str) -> dict:
    """利用 NetworkX 检索指定节点的 1 跳关联邻居与边，返回子图。"""
    with _lock:
        G = build_nx()
        if node_id not in G:
            raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")

        neighbors = set(G.neighbors(node_id)) | set(G.predecessors(node_id))
        sub_nodes = [dict(G.nodes[n]) for n in neighbors]
        sub_edges = [
            dict(G.edges[u, v])
            for u, v in G.edges
            if u == node_id or v == node_id or (u in neighbors and v in neighbors)
        ]
        return {"nodes": sub_nodes, "edges": sub_edges}


# ---------------------------------------------------------------------------
# API: 节点增删改
# ---------------------------------------------------------------------------
@app.post("/api/node")
def upsert_node(node: NodeIn) -> dict:
    """新增或更新节点信息（含 description 描述字段）。"""
    with _lock:
        for i, n in enumerate(graph_data["nodes"]):
            if n["id"] == node.id:
                graph_data["nodes"][i] = node.model_dump()
                return {"status": "updated", "node": graph_data["nodes"][i]}
        graph_data["nodes"].append(node.model_dump())
        return {"status": "created", "node": node.model_dump()}


@app.delete("/api/node/{node_id}")
def delete_node(node_id: str) -> dict:
    """从内存中移除节点，并级联删除所有关联边。"""
    with _lock:
        before = len(graph_data["nodes"])
        graph_data["nodes"] = [n for n in graph_data["nodes"] if n["id"] != node_id]
        removed_edges = [
            e for e in graph_data["edges"] if e["source"] == node_id or e["target"] == node_id
        ]
        graph_data["edges"] = [
            e for e in graph_data["edges"] if e["source"] != node_id and e["target"] != node_id
        ]
        if len(graph_data["nodes"]) == before:
            raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
        return {
            "status": "deleted",
            "node_id": node_id,
            "removed_edges": len(removed_edges),
        }


# ---------------------------------------------------------------------------
# API: 关系增改
# ---------------------------------------------------------------------------
@app.post("/api/edge")
def upsert_edge(edge: EdgeIn) -> dict:
    """新增或更新关系。"""
    with _lock:
        G = build_nx()
        if edge.source not in G:
            raise HTTPException(status_code=404, detail=f"源节点不存在: {edge.source}")
        if edge.target not in G:
            raise HTTPException(status_code=404, detail=f"目标节点不存在: {edge.target}")

        for i, e in enumerate(graph_data["edges"]):
            if e["id"] == edge.id:
                graph_data["edges"][i] = edge.model_dump()
                return {"status": "updated", "edge": graph_data["edges"][i]}
        graph_data["edges"].append(edge.model_dump())
        return {"status": "created", "edge": edge.model_dump()}


# ---------------------------------------------------------------------------
# API: 持久化保存
# ---------------------------------------------------------------------------
@app.post("/api/save")
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
# API: GraphRAG 检索上下文（1~2 跳子图 → Prompt Context）
# ---------------------------------------------------------------------------
@app.get("/api/rag/context/{node_id}")
def rag_context(node_id: str) -> dict:
    """
    根据指定节点 ID，提取其 1~2 跳的子图语义三元组与实体描述，
    拼接并返回一段完整的检索上下文文本（Prompt Context）。
    """
    with _lock:
        G = build_nx()
        if node_id not in G:
            raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")

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
        lines.append(f"- {focus.get('name', node_id)}（{focus.get('type', 'Unknown')}）：{focus.get('description', '')}")

        def _triplets(nodes: set, label: str) -> None:
            if not nodes:
                return
            lines.append(f"## {label}（语义三元组）")
            for u, v, data in G.edges(data=True):
                if (u in nodes or v in nodes) and (
                    u == node_id or v == node_id or (u in nodes and v in nodes)
                ):
                    src = G.nodes[u].get("name", u)
                    dst = G.nodes[v].get("name", v)
                    rel = data.get("relation", "RELATED_TO")
                    desc = data.get("description", "")
                    w = data.get("weight", 0.5)
                    lines.append(f"- ({src}) --[{rel} (weight={w})]--> ({dst})：{desc}")

        _triplets(hop1, "1 跳关系")
        _triplets(hop2, "2 跳关系")

        # 关联文本溯源
        chunks = focus.get("source_chunks", [])
        if chunks:
            lines.append("## 关联文本溯源（Source Chunks）")
            for c in chunks:
                lines.append(f"- {c}")

        return {"node_id": node_id, "context": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 静态文件托管（单文件前端）
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)