"""
========================================
Chat API - 聊天与会话路由
========================================
功能: 聊天SSE流式接口、会话管理、TODO查询、对话历史
 作者: CuteCuteYu
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from web.chat_handler import chat_handler
from web.chat_history_store import (
    append_message,
    delete_thread,
    list_sessions,
    load_thread,
)
from web.conversation import create_todo_for_request, get_todo_manager, new_chat
from web.sessions import (
    get_or_create_session,
    is_safe_thread_id,
    remove_session,
    sessions,
)
from web.sse import sse_format
from web.task_analyzer import check_task_completed
from web.todo_manager import TodoManager

logger = logging.getLogger(__name__)

router = APIRouter()

# chat_handler 是全局单例，串行化处理避免并发请求互相串会话
_chat_lock = asyncio.Lock()


# ═══════════════════════════════════════════════════════════════════════
# 请求模型定义 (Pydantic BaseModel)
# ═══════════════════════════════════════════════════════════════════════


class ChatRequest(BaseModel):
    """聊天请求模型"""

    message: str  # 用户消息内容
    thread_id: str | None = None  # 可选的线程ID，用于继续之前的对话


class NewChatRequest(BaseModel):
    """新建对话请求模型"""

    thread_id: str | None = None  # 可选的指定线程ID


# ═══════════════════════════════════════════════════════════════════════
# SSE 流式聊天
# ═══════════════════════════════════════════════════════════════════════


async def _stream_agent_events(content: str, result: dict):
    """
    消费 chat_handler.chat_stream 的事件并转发为 SSE 帧，
    最终回复与详情写入 result 字典

    参数:
        content: 传给Agent的用户输入
        result: 输出容器，最终写入 "response" 与 "details"
    """
    async for event in chat_handler.chat_stream(content):
        event_type = event["type"]
        if event_type == "segment_start":
            yield sse_format({"type": "segment_start"})
        elif event_type == "token":
            yield sse_format({"type": "response", "content": event["content"]})
        elif event_type == "tool_call":
            yield sse_format(
                {
                    "type": "tool_call",
                    "name": event["name"],
                    "status": event["status"],
                }
            )
        elif event_type == "final":
            result["response"] = event["response"]
            result["details"] = event["details"]
    # 用最终完整文本覆盖流式渲染，保证权威内容
    if result["response"]:
        yield sse_format({"type": "response_final", "content": result["response"]})


async def stream_chat_response(message: str, thread_id: str | None):
    """
    流式推送聊天响应（真流式：token 级增量）

    使用Server-Sent Events (SSE) 协议将处理过程实时推送给前端

    参数:
        message: 用户发送的消息
        thread_id: 可选的线程ID

    生成:
        SSE格式的数据字符串，包含各种事件类型
    """
    async with _chat_lock:
        try:
            # 获取或创建会话
            session = get_or_create_session(thread_id)
            tid = session["thread_id"]

            # 切换到指定的会话
            chat_handler.thread_id = tid
            chat_handler.message_history.clear()

            # 保存用户消息到历史记录
            append_message(tid, "user", message)

            # 发送 thread_id 事件，让前端知道当前对话线程
            yield sse_format({"type": "thread_id", "thread_id": tid})

            # 判断是否是该线程的首次消息
            is_first_message = (
                not session.get("last_thread_id") or session["last_thread_id"] != tid
            )

            # 判断是否需要创建TODO（输入字符 >= 20 时才创建）
            need_todo = is_first_message and len(message.strip()) >= 20

            if need_todo:
                # 发送正在创建任务清单的状态
                yield sse_format({"type": "status", "message": "正在创建任务清单..."})

                # 调用AI生成任务清单
                todos = await asyncio.to_thread(create_todo_for_request, message)
                todo_items = [{"description": t, "completed": False} for t in todos]
                session["last_thread_id"] = tid

                # 发送创建的TODO列表
                yield sse_format({"type": "todo_created", "items": todo_items})

            # 初始响应状态
            status_msg = (
                "AI 正在思考..." if not need_todo else "AI 正在按任务清单执行..."
            )
            yield sse_format({"type": "status", "message": status_msg})

            # 流式执行并转发事件
            stream_result: dict = {}
            async for sse_frame in _stream_agent_events(message, stream_result):
                yield sse_frame
            response, details = (
                stream_result.get("response", ""),
                stream_result.get("details", {}),
            )

            # 获取工具调用信息作为最后动作
            last_action = ""
            if details.get("tool_calls_made"):
                tool_names = ", ".join(tc["name"] for tc in details["tool_calls_made"])
                last_action = f"调用工具: {tool_names}"
                yield sse_format(
                    {"type": "status", "message": f"执行工具: {tool_names}"}
                )

            # ═════════════════════════════════════════════════════════════
            # 自动迭代处理 - 检查任务完成状态并继续执行
            # ═════════════════════════════════════════════════════════════
            iteration = 0
            current_last_action = last_action

            # 循环检查直到达到最大迭代次数
            while iteration < session["max_auto_iterations"]:
                # 发送检查状态
                yield sse_format({"type": "status", "message": "检查任务完成状态..."})

                # 调用AI检查任务是否完成
                completed, next_action = await asyncio.to_thread(
                    check_task_completed, response, message, current_last_action
                )

                # 如果任务已完成
                if completed:
                    if next_action:
                        # 发送备注信息
                        yield sse_format({"type": "note", "content": next_action})
                    break

                # 如果有下一步操作，继续执行
                if not next_action:
                    break

                yield sse_format(
                    {
                        "type": "status",
                        "message": f"继续执行: {next_action[:50]}...",
                    }
                )
                yield sse_format({"type": "auto_continue", "content": next_action})

                # 继续流式执行
                async for sse_frame in _stream_agent_events(next_action, stream_result):
                    yield sse_frame
                response = stream_result.get("response", response)

                current_last_action = next_action
                iteration += 1

            # 任务完成后删除TODO
            todo_mgr = get_todo_manager()
            if todo_mgr.exists():
                todo_mgr.delete_todo()
                yield sse_format({"type": "todo_deleted"})

            # 保存助手回复到历史记录
            append_message(tid, "assistant", response, {"iterations": []})

            # 发送完成信号
            yield sse_format({"type": "done"})

        except Exception as e:
            # 捕获所有错误并发送给前端
            logger.exception("聊天处理异常")
            error_msg = str(e)
            # 根据错误类型转换错误信息为中文提示
            if "429" in error_msg or "rate limit" in error_msg.lower():
                error_msg = "API 限流，请稍后再试 (模型当前负载过高)"
            elif "timeout" in error_msg.lower():
                error_msg = "请求超时，请重试"
            elif "connection" in error_msg.lower():
                error_msg = "网络连接错误"

            # 发送错误事件
            yield sse_format({"type": "error", "message": error_msg})
            yield sse_format({"type": "done"})


# ═══════════════════════════════════════════════════════════════════════
# API端点定义
# ═══════════════════════════════════════════════════════════════════════


@router.post("/api/chat")
async def api_chat(req: ChatRequest):
    """
    聊天接口 - 发送消息并获取AI回复（流式响应）

    参数:
        req: ChatRequest对象，包含message和可选的thread_id

    返回:
        StreamingResponse: SSE格式的流式响应
    """
    # 验证消息不为空
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 返回流式响应
    return StreamingResponse(
        stream_chat_response(req.message, req.thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/api/new")
async def api_new_chat(req: NewChatRequest | None = None):
    """
    创建新对话

    参数:
        req: 可选的NewChatRequest对象

    返回:
        包含新创建的thread_id
    """
    new_chat()
    tid = chat_handler.current_thread_id
    get_or_create_session(tid)
    return {"thread_id": tid}


@router.get("/api/sessions")
async def api_list_sessions():
    """列出所有会话"""
    return {"sessions": list(sessions.keys())}


@router.get("/api/todo")
async def api_get_todo(thread_id: str):
    """
    获取当前TODO列表

    参数:
        thread_id: 线程ID

    返回:
        包含TODO任务列表、已完成数、总任务数等信息
    """
    if not is_safe_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="非法的线程ID")

    todo_mgr = TodoManager(thread_id)
    if not todo_mgr.exists():
        return {"exists": False}

    # 读取TODO任务
    tasks, _content = todo_mgr.read_todo()
    # 统计已完成任务数
    completed_count = sum(1 for t in tasks if t.get("completed", False))

    return {
        "exists": True,
        "tasks": tasks,
        "completed_count": completed_count,
        "total_count": len(tasks),
    }


# ═══════════════════════════════════════════════════════════════════════
# 对话历史
# ═══════════════════════════════════════════════════════════════════════


@router.get("/api/history")
async def api_get_history():
    """
    获取所有聊天历史会话列表

    返回:
        历史会话列表，按创建时间倒序排列
    """
    return {"history": list_sessions()}


@router.get("/api/history/{thread_id}")
async def api_get_chat_history(thread_id: str):
    """
    获取指定会话的聊天历史详情

    参数:
        thread_id: 会话线程ID

    返回:
        包含该会话的所有消息
    """
    try:
        data = load_thread(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法的线程ID")
    if data is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return data


@router.delete("/api/history/{thread_id}")
async def api_delete_history(thread_id: str):
    """
    删除指定会话

    同时删除会话历史文件和对应的TODO目录

    参数:
        thread_id: 要删除的会话线程ID

    返回:
        删除结果
    """
    if not is_safe_thread_id(thread_id):
        raise HTTPException(status_code=400, detail="非法的线程ID")

    deleted = delete_thread(thread_id)

    # 删除TODO目录
    todo_mgr = TodoManager(thread_id)
    if todo_mgr.exists():
        todo_mgr.delete_todo()
        deleted = True

    # 从会话字典中移除
    remove_session(thread_id)

    return {"deleted": deleted}
