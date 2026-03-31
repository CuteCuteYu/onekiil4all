"""
========================================
FastAPI Web Server - Web服务器模块
========================================
功能: 提供 REST API 接口供前端和其他程序调用
包括: 聊天接口、历史记录管理、技能列表、工具列表、热点资讯等
 作者: 上古必斩必杀
"""

# ═══════════════════════════════════════════════════════════════
# 导入必要的标准库模块
# ═══════════════════════════════════════════════════════════════

import asyncio
import uuid
import sys
import io
from contextlib import asynccontextmanager, contextmanager

# ═══════════════════════════════════════════════════════════════
# 导入FastAPI和相关依赖
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

# ═══════════════════════════════════════════════════════════════
# 导入项目内部模块
# ═══════════════════════════════════════════════════════════════

from web.chat_handler import chat_handler
from web.conversation import (
    new_chat,
    create_todo_for_request,
    get_thread_id,
    get_todo_manager,
)
from web.task_analyzer import check_task_completed


# ═══════════════════════════════════════════════════════════════
# 辅助函数：临时抑制标准输出
# ═══════════════════════════════════════════════════════════════


@contextmanager
def suppress_stdout():
    """
    临时抑制标准输出
    用途: 阻止AI处理过程中的调试信息输出到终端，保持界面整洁
    """
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout


# ═══════════════════════════════════════════════════════════════
# 请求模型定义 (Pydantic BaseModel)
# 用于API请求的参数验证
# ═══════════════════════════════════════════════════════════════


class ChatRequest(BaseModel):
    """聊天请求模型"""

    message: str  # 用户消息内容
    thread_id: str | None = None  # 可选的线程ID，用于继续之前的对话


class NewChatRequest(BaseModel):
    """新建对话请求模型"""

    thread_id: str | None = None  # 可选的指定线程ID


# ═══════════════════════════════════════════════════════════════
# 会话管理
# ═══════════════════════════════════════════════════════════════

# 会话存储字典，键为线程ID，值为会话信息字典
sessions: dict[str, dict] = {}


def get_or_create_session(thread_id: str | None) -> dict:
    """
    获取或创建会话
    如果传入的thread_id已存在则返回对应会话，否则创建新会话

    参数:
        thread_id: 线程ID，如果为None则创建新的

    返回:
        会话信息字典，包含thread_id、last_thread_id、max_auto_iterations等
    """
    # 如果线程ID存在，直接返回对应会话
    if thread_id and thread_id in sessions:
        return sessions[thread_id]

    # 生成新的线程ID
    new_tid = thread_id or str(uuid.uuid4())

    # 创建新会话信息
    session = {
        "thread_id": new_tid,
        "last_thread_id": None,  # 上一个线程ID（用于判断是否首次消息）
        "max_auto_iterations": 5,  # 最大自动迭代次数
    }

    # 保存会话并返回
    sessions[new_tid] = session
    return session


# ═══════════════════════════════════════════════════════════════
# FastAPI 应用初始化
# ═══════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI生命周期管理
    应用启动和关闭时的处理逻辑
    """
    print("Web server started")

    alert_queue: asyncio.Queue = app.state.alert_queue

    async def alert_checker():
        """后台告警检查任务，每秒执行一次"""
        import asyncio
        from web.trends import get_trends

        while True:
            try:
                await asyncio.sleep(1)

                trends = await asyncio.to_thread(get_trends, check_alerts=True)
                new_alerts = trends.get("new_alerts", [])

                for alert_event in new_alerts:
                    await alert_queue.put(alert_event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Alert check error: {e}")

    alert_checker_task = asyncio.create_task(alert_checker())

    yield

    alert_checker_task.cancel()
    try:
        await alert_checker_task
    except asyncio.CancelledError:
        pass
    print("Web server stopped")


# 创建FastAPI应用实例
app = FastAPI(
    title="上古必斩必杀 API",
    description="AI 聊天系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.alert_queue = asyncio.Queue()

# ═══════════════════════════════════════════════════════════════
# CORS中间件配置
# 允许跨域请求
# ═══════════════════════════════════════════════════════════════

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,  # 允许凭据
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# ═══════════════════════════════════════════════════════════════
# 静态文件服务挂载
# ═══════════════════════════════════════════════════════════════

# 挂载静态文件目录到 /static 路径
app.mount("/static", StaticFiles(directory="static"), name="static")


# ═══════════════════════════════════════════════════════════════
# 根路径路由 - 返回前端页面
# ═══════════════════════════════════════════════════════════════


@app.get("/")
async def index():
    """返回主页HTML文件"""
    return FileResponse("static/index.html")


@app.get("/alert")
async def alert_page(keyword: str | None = None):
    """返回告警详情页面"""
    return FileResponse("static/alert.html")


# ═══════════════════════════════════════════════════════════════
# API 路由定义
# ═══════════════════════════════════════════════════════════════


def stream_chat_response(message: str, thread_id: str | None):
    """
    流式推送聊天响应
    使用Server-Sent Events (SSE) 协议将处理过程实时推送给前端

    参数:
        message: 用户发送的消息
        thread_id: 可选的线程ID

    生成:
        SSE格式的数据字符串，包含各种事件类型
    """
    import json

    try:
        # 获取或创建会话
        session = get_or_create_session(thread_id)
        tid = session["thread_id"]

        # 切换到指定的会话
        chat_handler.thread_id = tid
        chat_handler.message_history.clear()

        # 保存用户消息到历史记录
        save_chat_message(tid, "user", message)

        # 发送 thread_id 事件，让前端知道当前对话线程
        yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': tid})}\n\n"

        # 抑制终端输出，包裹所有处理代码
        with suppress_stdout():
            # 判断是否是该线程的首次消息
            is_first_message = (
                not session.get("last_thread_id") or session["last_thread_id"] != tid
            )

            # 判断是否需要创建TODO（输入字符 >= 20 时才创建）
            message_length = len(message.strip())
            need_todo = is_first_message and message_length >= 20

            todo_items = []
            if need_todo:
                # 发送正在创建任务清单的状态
                yield f"data: {json.dumps({'type': 'status', 'message': '正在创建任务清单...'})}\n\n"

                # 调用AI生成任务清单
                todos = create_todo_for_request(message)
                todo_items = [{"description": t, "completed": False} for t in todos]
                session["last_thread_id"] = tid

                # 发送创建的TODO列表
                yield f"data: {json.dumps({'type': 'todo_created', 'items': todo_items})}\n\n"

            # 初始响应状态
            status_msg = (
                "AI 正在思考..." if not need_todo else "AI 正在按任务清单执行..."
            )
            yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"

            # 使用同步聊天方法处理请求
            response, details = chat_handler.chat(message)

            # 获取工具调用信息作为最后动作
            last_action = ""
            if details.get("tool_calls_made"):
                # 格式化工具名称列表
                tool_names = ", ".join(tc["name"] for tc in details["tool_calls_made"])
                last_action = f"调用工具: {tool_names}"
                yield f"data: {json.dumps({'type': 'status', 'message': f'执行工具: {tool_names}'})}\n\n"

                # 逐个发送工具调用事件（实时发送）
                for i, tc in enumerate(details["tool_calls_made"]):
                    # 发送工具开始调用事件
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'status': '开始调用...', 'index': i, 'total': len(details['tool_calls_made'])})}\n\n"

                    # 发送工具执行中事件
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'status': '执行中...', 'index': i, 'total': len(details['tool_calls_made'])})}\n\n"

                    # 发送工具完成事件
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'status': '✓ 完成', 'index': i, 'total': len(details['tool_calls_made'])})}\n\n"

                # 发送批量工具调用事件用于兼容
                tools_list = [{"name": tc["name"]} for tc in details["tool_calls_made"]]
                yield f"data: {json.dumps({'type': 'tool_calls', 'tools': tools_list})}\n\n"

            # 发送最终响应内容
            yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"

            # ═══════════════════════════════════════════════════════
            # 自动迭代处理 - 检查任务完成状态并继续执行
            # ═══════════════════════════════════════════════════════
            iteration = 0
            current_last_action = last_action

            # 循环检查直到达到最大迭代次数
            while iteration < session["max_auto_iterations"]:
                # 发送检查状态
                yield f"data: {json.dumps({'type': 'status', 'message': '检查任务完成状态...'})}\n\n"

                # 调用AI检查任务是否完成
                completed, next_action, is_int = check_task_completed(
                    response, message, current_last_action
                )

                # 如果用户中断
                if is_int:
                    yield f"data: {json.dumps({'type': 'status', 'message': '用户中断'})}\n\n"
                    break

                # 如果任务已完成
                if completed:
                    if next_action:
                        # 发送备注信息
                        yield f"data: {json.dumps({'type': 'note', 'content': next_action})}\n\n"
                    break

                # 如果有下一步操作，继续执行
                if next_action:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'继续执行: {next_action[:50]}...'})}\n\n"
                    yield f"data: {json.dumps({'type': 'auto_continue', 'content': next_action})}\n\n"

                    # 继续调用AI执行
                    response, cont_details = chat_handler.chat(next_action)
                    yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"

                    # 如果有工具调用，发送状态
                    if cont_details.get("tool_calls_made"):
                        tool_names = ", ".join(
                            tc["name"] for tc in cont_details["tool_calls_made"]
                        )
                        yield f"data: {json.dumps({'type': 'status', 'message': f'执行工具: {tool_names}'})}\n\n"
                        yield f"data: {json.dumps({'type': 'tool_calls', 'tools': [{'name': tc['name']} for tc in cont_details['tool_calls_made']]})}\n\n"

                    current_last_action = next_action
                    iteration += 1
                else:
                    break

            # 任务完成后删除TODO
            todo_mgr = get_todo_manager()
            if todo_mgr.exists():
                todo_mgr.delete_todo()
                yield f"data: {json.dumps({'type': 'todo_deleted'})}\n\n"

        # 保存助手回复到历史记录（在suppress_stdout外面）
        save_chat_message(tid, "assistant", response, {"iterations": []})

        # 发送完成信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        # 捕获所有错误并发送给前端
        import traceback

        error_msg = str(e)
        # 根据错误类型转换错误信息为中文提示
        if "429" in error_msg or "rate limit" in error_msg.lower():
            error_msg = "API 限流，请稍后再试 (模型当前负载过高)"
        elif "timeout" in error_msg.lower():
            error_msg = "请求超时，请重试"
        elif "connection" in error_msg.lower():
            error_msg = "网络连接错误"

        # 发送错误事件
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ═══════════════════════════════════════════════════════════════
# API端点定义
# ═══════════════════════════════════════════════════════════════


@app.post("/api/chat")
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


@app.get("/api/todo")
async def api_get_todo(thread_id: str):
    """
    获取当前TODO列表

    参数:
        thread_id: 线程ID

    返回:
        包含TODO任务列表、已完成数、总任务数等信息
    """
    todo_mgr = get_todo_manager_by_tid(thread_id)
    if not todo_mgr.exists():
        return {"exists": False}

    # 读取TODO任务
    tasks, _ = todo_mgr.read_todo()
    # 统计已完成任务数
    completed_count = sum(1 for t in tasks if t.get("completed", False))

    return {
        "exists": True,
        "tasks": tasks,
        "completed_count": completed_count,
        "total_count": len(tasks),
    }


@app.post("/api/new")
async def api_new_chat(req: NewChatRequest | None = None):
    """
    创建新对话

    参数:
        req: 可选的NewChatRequest对象

    返回:
        包含新创建的thread_id
    """
    with suppress_stdout():
        new_chat()
        tid = chat_handler.current_thread_id
    get_or_create_session(tid)
    return {"thread_id": tid}


@app.get("/api/sessions")
async def api_list_sessions():
    """列出所有会话"""
    return {"sessions": list(sessions.keys())}


@app.get("/api/skills")
async def api_list_skills():
    """
    列出可用的技能列表

    读取 ~/.claude/skills 目录下的技能定义文件

    返回:
        技能列表，每个技能包含id和description
    """
    from pathlib import Path

    skills_dir = Path.home() / ".claude" / "skills"
    skills = []

    # 遍历技能目录
    if skills_dir.exists():
        for folder in skills_dir.iterdir():
            if folder.is_dir():
                skill_md = folder / "SKILL.md"
                if skill_md.exists():
                    try:
                        # 读取技能文件内容
                        content = skill_md.read_text(encoding="utf-8")
                        # 提取第一行作为描述
                        lines = content.split("\n")
                        desc = lines[0] if lines else folder.name
                        # 去除Markdown标题符号
                        if desc.startswith("#"):
                            desc = desc.lstrip("#").strip()
                        skills.append({"id": folder.name, "description": desc})
                    except Exception:
                        skills.append({"id": folder.name, "description": ""})

    # 按技能ID排序返回
    return {"skills": sorted(skills, key=lambda x: x["id"])}


@app.get("/api/tools")
async def api_list_tools():
    """
    列出可用的工具列表

    返回:
        工具列表，每个工具包含name和description
    """
    from agent_set.tools_set import tools

    tool_list = []
    for tool in tools:
        tool_list.append(
            {
                "name": tool.name,
                "description": tool.description.strip(),
            }
        )
    return {"tools": tool_list}


@app.get("/api/history")
async def api_get_history():
    """
    获取所有聊天历史会话列表

    返回:
        历史会话列表，按创建时间倒序排列
    """
    from pathlib import Path
    import json

    history_dir = Path("chat_history")
    history = []

    # 遍历历史记录目录
    if history_dir.exists():
        for file in history_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                history.append(
                    {
                        "thread_id": data.get("thread_id", file.stem),
                        "created_at": data.get("created_at"),
                        "last_message": data.get("last_message", ""),
                    }
                )
            except Exception:
                pass

    # 按创建时间倒序返回
    return {
        "history": sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
    }


@app.get("/api/history/{thread_id}")
async def api_get_chat_history(thread_id: str):
    """
    获取指定会话的聊天历史详情

    参数:
        thread_id: 会话线程ID

    返回:
        包含该会话的所有消息
    """
    from pathlib import Path
    import json

    history_file = Path("chat_history") / f"{thread_id}.json"
    if not history_file.exists():
        raise HTTPException(status_code=404, detail="会话不存在")

    try:
        data = json.loads(history_file.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {e}")


@app.get("/api/trends")
async def api_get_trends():
    """获取热门搜索和情报信息"""
    from web.trends import get_trends

    return get_trends()


@app.get("/api/alerts")
async def api_get_alerts():
    """获取所有告警规则"""
    from web.alert_manager import alert_manager

    alerts = alert_manager.get_all_alerts()
    return {"alerts": [a.to_dict() for a in alerts]}


@app.post("/api/alerts")
async def api_create_alert(request: Request):
    """创建新的告警规则"""
    from web.alert_manager import alert_manager

    try:
        body = await request.json()
        keyword = body.get("keyword", "").strip()
        if not keyword:
            raise HTTPException(status_code=400, detail="关键词不能为空")

        alert = alert_manager.add_alert(keyword)
        return {"alert": alert.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {e}")


@app.delete("/api/alerts/{alert_id}")
async def api_delete_alert(alert_id: str):
    """删除告警规则"""
    from web.alert_manager import alert_manager

    deleted = alert_manager.remove_alert(alert_id)
    if deleted:
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="告警规则不存在")


@app.post("/api/alerts/{alert_id}/toggle")
async def api_toggle_alert(alert_id: str):
    """切换告警启用/禁用状态"""
    from web.alert_manager import alert_manager

    success = alert_manager.toggle_alert(alert_id)
    if success:
        alerts = alert_manager.get_all_alerts()
        alert = next((a for a in alerts if a.id == alert_id), None)
        return {"alert": alert.to_dict() if alert else None}
    raise HTTPException(status_code=404, detail="告警规则不存在")


@app.get("/api/alerts/history")
async def api_get_alert_history(limit: int = 50):
    """获取告警历史记录"""
    from web.alert_manager import alert_manager

    history = alert_manager.get_history(limit)
    return {"history": [h.to_dict() for h in history]}


@app.delete("/api/alerts/history/all")
async def api_clear_alert_history_all():
    """清空告警历史"""
    from web.alert_manager import alert_manager

    alert_manager.clear_history()
    return {"cleared": True}


@app.get("/api/alerts/timeline/{keyword}")
async def api_get_alert_timeline(keyword: str):
    """获取关键词的事件时间线"""
    from web.alert_manager import alert_manager

    timeline = alert_manager.get_timeline(keyword)
    return {"keyword": keyword, "timeline": [h.to_dict() for h in timeline]}


@app.delete("/api/alerts/history")
async def api_clear_alert_history():
    """清空告警历史"""
    from web.alert_manager import alert_manager

    alert_manager.clear_history()
    return {"cleared": True}


@app.get("/api/alerts/stream")
async def api_alerts_stream(request: Request):
    """
    告警事件流 - SSE
    后台定时检查并推送新告警事件
    """
    alert_queue = request.app.state.alert_queue

    async def event_generator():
        while True:
            try:
                alert_event = await asyncio.wait_for(alert_queue.get(), timeout=30)
                yield f"data: {json.dumps({'type': 'alert', 'event': alert_event})}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            except GeneratorExit:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


import json


@app.delete("/api/history/{thread_id}")
async def api_delete_history(thread_id: str):
    """
    删除指定会话

    同时删除会话历史文件和对应的TODO目录

    参数:
        thread_id: 要删除的会话线程ID

    返回:
        删除结果
    """
    from pathlib import Path
    import shutil

    history_file = Path("chat_history") / f"{thread_id}.json"
    todo_dir = Path("todo") / thread_id

    deleted = False
    # 删除历史记录文件
    if history_file.exists():
        history_file.unlink()
        deleted = True
    # 删除TODO目录
    if todo_dir.exists():
        shutil.rmtree(todo_dir)
        deleted = True

    # 从会话字典中移除
    if thread_id in sessions:
        del sessions[thread_id]

    return {"deleted": deleted}


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════


def save_chat_message(
    thread_id: str, role: str, content: str, metadata: dict | None = None
):
    """
    保存聊天消息到历史文件

    参数:
        thread_id: 线程ID
        role: 消息角色 (user/assistant)
        content: 消息内容
        metadata: 可选的元数据
    """
    from pathlib import Path
    import json
    from datetime import datetime

    # 确保历史目录存在
    history_dir = Path("chat_history")
    history_dir.mkdir(exist_ok=True)

    history_file = history_dir / f"{thread_id}.json"

    # 读取现有数据或创建新数据
    if history_file.exists():
        try:
            data = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            data = {
                "thread_id": thread_id,
                "messages": [],
                "created_at": datetime.now().isoformat(),
            }
    else:
        data = {
            "thread_id": thread_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
        }

    # 构建消息对象
    message: dict = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    if metadata is not None:
        message["metadata"] = metadata

    # 添加消息
    data["messages"].append(message)
    data["last_message"] = content[:100] if content else ""
    data["updated_at"] = datetime.now().isoformat()

    # 写入文件
    history_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_todo_manager_by_tid(thread_id: str):
    """
    根据thread_id获取对应的TODO管理器

    参数:
        thread_id: 线程ID

    返回:
        TodoManager实例
    """
    from web.todo_manager import TodoManager

    return TodoManager(thread_id)


# ═══════════════════════════════════════════════════════════════
# 主程序入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    # 启动uvicorn服务器
    uvicorn.run("web.web_server:app", host="0.0.0.0", port=8000, reload=True)
