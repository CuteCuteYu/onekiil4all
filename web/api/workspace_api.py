"""
========================================
Workspace API - 工作区路由
========================================
功能: 工作区状态查询与设置。
Agent 初始化前必须先选择工作区文件夹，
之后所有产物默认保存在该文件夹中。
 作者: CuteCuteYu
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent_set import workspace

logger = logging.getLogger(__name__)

router = APIRouter()


class WorkspaceRequest(BaseModel):
    """工作区设置请求模型"""

    path: str  # 用户选择的文件夹路径


@router.get("/api/workspace")
async def api_get_workspace():
    """
    查询当前工作区状态

    返回:
        {"ready": bool, "workspace": str | None}
        ready 为 False 时前端应显示工作区选择页，Agent loop 拒绝启动
    """
    ws = workspace.get_workspace()
    return {"ready": ws is not None, "workspace": str(ws) if ws else None}


@router.post("/api/workspace")
async def api_set_workspace(req: WorkspaceRequest):
    """
    设置工作区（用户在页面选择文件夹后调用）

    参数:
        req.path: 文件夹绝对路径

    返回:
        {"ready": True, "workspace": 规范化后的路径}

    异常:
        400: 路径不存在或不是文件夹
    """
    try:
        resolved = workspace.set_workspace(req.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.info("工作区已设置: %s", resolved)
    return {"ready": True, "workspace": str(resolved)}


@router.delete("/api/workspace")
async def api_clear_workspace():
    """清除工作区选择（回到未初始化状态）"""
    workspace.clear_workspace()
    return {"ready": False, "workspace": None}
