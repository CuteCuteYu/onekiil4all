"""
========================================
Workspace API - 工作区路由
========================================
功能: 工作区状态查询与设置。
Agent 初始化前必须先选择工作区文件夹，
之后所有产物默认保存在该文件夹中。
Browse 支持由后端弹出系统原生文件夹选择框。
 作者: CuteCuteYu
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent_set import workspace

logger = logging.getLogger(__name__)

router = APIRouter()


class WorkspaceRequest(BaseModel):
    """工作区设置请求模型"""

    path: str  # 用户选择的文件夹路径


def _pick_folder_dialog() -> str | None:
    """
    弹出 Windows 系统原生文件夹选择框（阻塞式，需在线程中调用）

    返回:
        用户选择的文件夹绝对路径；取消时返回 None

    异常:
        RuntimeError: 非 Windows 平台或缺少 pywin32
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as e:
        raise RuntimeError("当前环境不支持图形文件夹选择（缺少 tkinter）") from e

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # 保证对话框置顶
    try:
        root.update_idletasks()
        folder = filedialog.askdirectory(title="选择工作区文件夹")
    finally:
        root.destroy()
    return folder or None


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


@router.get("/api/workspace/browse")
async def api_browse_workspace():
    """
    弹出系统文件夹选择框（BROWSE 按钮调用）

    对话框为模态阻塞，放到线程池避免卡住事件循环。

    返回:
        {"path": str | None} 取消时 path 为 None
    """
    try:
        folder = await asyncio.to_thread(_pick_folder_dialog)
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    return {"path": folder}


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
