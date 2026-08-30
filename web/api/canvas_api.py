"""
========================================
Canvas API - 情报分析图谱画板路由
========================================
功能: 画板管理 / 图谱 CRUD / 类型管理 / 1 跳展开 / RAG 上下文
 作者: 上古必斩必杀
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from web.intelligence.graph_board import (
    GraphBoardError,
    create_board,
    delete_board,
    delete_node,
    delete_type,
    expand_node,
    get_boards,
    get_graph,
    get_types,
    graph_status,
    open_board,
    rag_context,
    rename_board,
    save,
    upsert_edge,
    upsert_node,
    upsert_type,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic 请求模型（严格遵循 GraphRAG 字段规范）
# ---------------------------------------------------------------------------
class NodeIn(BaseModel):
    id: str = Field(..., description="节点唯一标识，如 ent_baoyu")
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型，如 ThreatActor / Malware")
    description: str = Field(
        "", description="自然语言描述，用于 GraphRAG 生成 Entity Embedding"
    )
    properties: dict = Field(default_factory=dict, description="结构化元数据")
    source_chunks: list = Field(
        default_factory=list, description="关联的原始文本片段 ID 或简述"
    )


class EdgeIn(BaseModel):
    id: str = Field(..., description="关系唯一标识")
    source: str = Field(..., description="源节点 ID")
    target: str = Field(..., description="目标节点 ID")
    relation: str = Field(..., description="关系动词，大写下划线，如 CONTROLS / USES")
    description: str = Field(
        "", description="关系的语义描述，用于 RAG 检索提供边上下文"
    )
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


def _raise_err(exc: GraphBoardError) -> None:
    """将画板业务错误转换为 HTTP 异常。"""
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


# ---------------------------------------------------------------------------
# API: 画板管理（独立文件管理）
# ---------------------------------------------------------------------------
@router.get("/api/boards")
async def api_get_boards():
    """列出所有画板及当前打开的画板。"""
    return await asyncio.to_thread(get_boards)


@router.post("/api/boards")
async def api_create_board(body: BoardCreate):
    """创建全新的空画板。"""
    try:
        return await asyncio.to_thread(create_board, body.name)
    except GraphBoardError as e:
        _raise_err(e)


@router.post("/api/boards/open")
async def api_open_board(body: BoardOpen):
    """打开指定画板并载入内存，返回画板数据。"""
    try:
        return await asyncio.to_thread(open_board, body.name)
    except GraphBoardError as e:
        _raise_err(e)


@router.post("/api/boards/rename")
async def api_rename_board(body: BoardRename):
    """重命名画板。"""
    try:
        return await asyncio.to_thread(rename_board, body.old_name, body.new_name)
    except GraphBoardError as e:
        _raise_err(e)


@router.delete("/api/boards/{name}")
async def api_delete_board(name: str):
    """删除画板文件；若删除的是当前画板，则切换到第一个可用画板。"""
    try:
        return await asyncio.to_thread(delete_board, name)
    except GraphBoardError as e:
        _raise_err(e)


# ---------------------------------------------------------------------------
# API: 图数据
# ---------------------------------------------------------------------------
@router.get("/api/graph")
async def api_get_graph():
    """读取内存中的全局图数据。"""
    return await asyncio.to_thread(get_graph)


@router.get("/api/graph/status")
async def api_get_graph_status():
    """获取当前画板状态：是否已打开、是否已保存（用于 GraphRAG 接入判定）。"""
    return await asyncio.to_thread(graph_status)


# ---------------------------------------------------------------------------
# API: 实体类型管理（支持用户自定义实体类型）
# ---------------------------------------------------------------------------
@router.get("/api/types")
async def api_get_types():
    """获取全部实体类型定义（内置 + 自定义）。"""
    return await asyncio.to_thread(get_types)


@router.post("/api/types")
async def api_upsert_type(t: TypeIn):
    """新增或更新自定义实体类型（名称/标签/颜色/形状）。"""
    try:
        return await asyncio.to_thread(upsert_type, t.name, t.label, t.color, t.shape)
    except GraphBoardError as e:
        _raise_err(e)


@router.delete("/api/types/{type_name}")
async def api_delete_type(type_name: str):
    """删除自定义实体类型（内置类型不可删除）。"""
    try:
        return await asyncio.to_thread(delete_type, type_name)
    except GraphBoardError as e:
        _raise_err(e)


# ---------------------------------------------------------------------------
# API: 1 跳展开
# ---------------------------------------------------------------------------
@router.get("/api/expand/{node_id}")
async def api_expand_node(node_id: str):
    """利用 NetworkX 检索指定节点的 1 跳关联邻居与边，返回子图。"""
    try:
        return await asyncio.to_thread(expand_node, node_id)
    except GraphBoardError as e:
        _raise_err(e)


# ---------------------------------------------------------------------------
# API: 节点增删改
# ---------------------------------------------------------------------------
@router.post("/api/node")
async def api_upsert_node(node: NodeIn):
    """新增或更新节点信息（含 description 描述字段）。"""
    return await asyncio.to_thread(upsert_node, node.model_dump())


@router.delete("/api/node/{node_id}")
async def api_delete_node(node_id: str):
    """从内存中移除节点，并级联删除所有关联边。"""
    try:
        return await asyncio.to_thread(delete_node, node_id)
    except GraphBoardError as e:
        _raise_err(e)


# ---------------------------------------------------------------------------
# API: 关系增改
# ---------------------------------------------------------------------------
@router.post("/api/edge")
async def api_upsert_edge(edge: EdgeIn):
    """新增或更新关系。"""
    try:
        return await asyncio.to_thread(upsert_edge, edge.model_dump())
    except GraphBoardError as e:
        _raise_err(e)


# ---------------------------------------------------------------------------
# API: 持久化保存
# ---------------------------------------------------------------------------
@router.post("/api/save")
async def api_save():
    """将当前内存图数据全量持久化写回当前画板文件。"""
    try:
        return await asyncio.to_thread(save)
    except GraphBoardError as e:
        _raise_err(e)


# ---------------------------------------------------------------------------
# API: GraphRAG 检索上下文（1~2 跳子图 → Prompt Context）
# ---------------------------------------------------------------------------
@router.get("/api/rag/context/{node_id}")
async def api_rag_context(node_id: str):
    """
    根据指定节点 ID，提取其 1~2 跳的子图语义三元组与实体描述，
    拼接并返回一段完整的检索上下文文本（Prompt Context）。
    """
    try:
        return await asyncio.to_thread(rag_context, node_id)
    except GraphBoardError as e:
        _raise_err(e)
