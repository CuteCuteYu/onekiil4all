"""
FastAPI Web Server
提供 REST API 接口供前端和其他程序调用
"""

import asyncio
import uuid
import sys
import io
from contextlib import asynccontextmanager, contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from web.chat_handler import chat_handler
from web.conversation import (
    new_chat,
    create_todo_for_request,
    get_thread_id,
    get_todo_manager,
)
from web.task_analyzer import check_task_completed


@contextmanager
def suppress_stdout():
    """临时抑制标准输出"""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout


# --- 请求模型 ---


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class NewChatRequest(BaseModel):
    thread_id: str | None = None


# --- 会话管理 ---

sessions: dict[str, dict] = {}


def get_or_create_session(thread_id: str | None) -> dict:
    """获取或创建会话"""
    if thread_id and thread_id in sessions:
        return sessions[thread_id]

    new_tid = thread_id or str(uuid.uuid4())
    session = {
        "thread_id": new_tid,
        "last_thread_id": None,
        "max_auto_iterations": 5,
    }
    sessions[new_tid] = session
    return session


# --- FastAPI App ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Web server started")
    yield
    print("Web server stopped")


app = FastAPI(
    title="onekiil4all API",
    description="AI 聊天系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


# --- API 路由 ---


def stream_chat_response(message: str, thread_id: str | None):
    """流式推送聊天响应"""
    import json

    try:
        session = get_or_create_session(thread_id)
        tid = session["thread_id"]

        # 如果请求指定了不同的 thread_id，切换会话
        if thread_id and chat_handler.thread_id != tid:
            chat_handler.thread_id = tid

        # 保存用户消息
        save_chat_message(tid, "user", message)

        # 发送 thread_id
        yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': tid})}\n\n"

        # 抑制终端输出，包裹所有处理代码
        with suppress_stdout():
            is_first_message = (
                not session.get("last_thread_id") or session["last_thread_id"] != tid
            )

            # 判断是否需要创建 TODO（输入字符 >= 20 时才创建）
            message_length = len(message.strip())
            need_todo = is_first_message and message_length >= 20

            todo_items = []
            if need_todo:
                yield f"data: {json.dumps({'type': 'status', 'message': '正在创建任务清单...'})}\n\n"
                todos = create_todo_for_request(message)
                todo_items = [{"description": t, "completed": False} for t in todos]
                session["last_thread_id"] = tid

                # 发送创建的 TODO
                yield f"data: {json.dumps({'type': 'todo_created', 'items': todo_items})}\n\n"

            # 初始响应
            status_msg = (
                "AI 正在思考..." if not need_todo else "AI 正在按任务清单执行..."
            )
            yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"

            # 使用同步聊天方法，但实时发送工具调用事件
            response, details = chat_handler.chat(message)

            # 获取工具调用作为 last_action
            last_action = ""
            if details.get("tool_calls_made"):
                tool_names = ", ".join(tc["name"] for tc in details["tool_calls_made"])
                last_action = f"调用工具: {tool_names}"
                yield f"data: {json.dumps({'type': 'status', 'message': f'执行工具: {tool_names}'})}\n\n"

                # 逐个发送工具调用事件（实时发送，不是模拟）
                for i, tc in enumerate(details["tool_calls_made"]):
                    # 立即发送工具开始调用事件
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'status': '开始调用...', 'index': i, 'total': len(details['tool_calls_made'])})}\n\n"

                    # 立即发送工具执行中事件
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'status': '执行中...', 'index': i, 'total': len(details['tool_calls_made'])})}\n\n"

                    # 立即发送工具完成事件
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'status': '✓ 完成', 'index': i, 'total': len(details['tool_calls_made'])})}\n\n"

                # 仍然发送批量事件用于兼容
                yield f"data: {json.dumps({'type': 'tool_calls', 'tools': [{'name': tc['name']} for tc in details['tool_calls_made']]})}\n\n"

            # 发送最终响应
            yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"

            # 自动迭代
            iteration = 0
            current_last_action = last_action

            while iteration < session["max_auto_iterations"]:
                yield f"data: {json.dumps({'type': 'status', 'message': '检查任务完成状态...'})}\n\n"
                completed, next_action, is_int = check_task_completed(
                    response, message, current_last_action
                )

                if is_int:
                    yield f"data: {json.dumps({'type': 'status', 'message': '用户中断'})}\n\n"
                    break

                if completed:
                    if next_action:
                        yield f"data: {json.dumps({'type': 'note', 'content': next_action})}\n\n"
                    break

                if next_action:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'继续执行: {next_action[:50]}...'})}\n\n"
                    yield f"data: {json.dumps({'type': 'auto_continue', 'content': next_action})}\n\n"

                    response, cont_details = chat_handler.chat(next_action)
                    yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"

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

            # 任务完成后删除 TODO
            todo_mgr = get_todo_manager()
            if todo_mgr.exists():
                todo_mgr.delete_todo()
                yield f"data: {json.dumps({'type': 'todo_deleted'})}\n\n"

        # 保存助手回复（在 suppress_stdout 外面）
        save_chat_message(tid, "assistant", response, {"iterations": []})

        # 发送完成信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        # 捕获所有错误并发送给前端
        import traceback

        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower():
            error_msg = "API 限流，请稍后再试 (模型当前负载过高)"
        elif "timeout" in error_msg.lower():
            error_msg = "请求超时，请重试"
        elif "connection" in error_msg.lower():
            error_msg = "网络连接错误"

        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """发送消息并获取 AI 回复（流式）"""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    return StreamingResponse(
        stream_chat_response(req.message, req.thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/api/todo")
async def api_get_todo(thread_id: str):
    """获取当前 TODO 列表"""
    todo_mgr = get_todo_manager_by_tid(thread_id)
    if not todo_mgr.exists():
        return {"exists": False}

    tasks, _ = todo_mgr.read_todo()
    completed_count = sum(1 for t in tasks if t.get("completed", False))
    return {
        "exists": True,
        "tasks": tasks,
        "completed_count": completed_count,
        "total_count": len(tasks),
    }


@app.post("/api/new")
async def api_new_chat(req: NewChatRequest | None = None):
    """创建新对话"""
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
    """列出可用的 skills"""
    from pathlib import Path

    skills_dir = Path.home() / ".claude" / "skills"
    skills = []
    if skills_dir.exists():
        for folder in skills_dir.iterdir():
            if folder.is_dir():
                skill_md = folder / "SKILL.md"
                if skill_md.exists():
                    try:
                        content = skill_md.read_text(encoding="utf-8")
                        # 提取第一行作为描述
                        lines = content.split("\n")
                        desc = lines[0] if lines else folder.name
                        if desc.startswith("#"):
                            desc = desc.lstrip("#").strip()
                        skills.append({"id": folder.name, "description": desc})
                    except Exception:
                        skills.append({"id": folder.name, "description": ""})
    return {"skills": sorted(skills, key=lambda x: x["id"])}


@app.get("/api/tools")
async def api_list_tools():
    """列出可用的 tools"""
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
    """获取所有聊天历史会话"""
    from pathlib import Path
    import json

    history_dir = Path("chat_history")
    history = []
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
    return {
        "history": sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
    }


@app.get("/api/history/{thread_id}")
async def api_get_chat_history(thread_id: str):
    """获取指定会话的聊天历史"""
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


@app.delete("/api/history/{thread_id}")
async def api_delete_chat_history(thread_id: str):
    """删除指定会话"""
    from pathlib import Path
    import shutil

    history_file = Path("chat_history") / f"{thread_id}.json"
    todo_dir = Path("todo") / thread_id

    deleted = False
    if history_file.exists():
        history_file.unlink()
        deleted = True
    if todo_dir.exists():
        shutil.rmtree(todo_dir)
        deleted = True

    if thread_id in sessions:
        del sessions[thread_id]

    return {"deleted": deleted}


def save_chat_message(
    thread_id: str, role: str, content: str, metadata: dict | None = None
):
    """保存聊天消息到历史"""
    from pathlib import Path
    import json
    from datetime import datetime

    history_dir = Path("chat_history")
    history_dir.mkdir(exist_ok=True)

    history_file = history_dir / f"{thread_id}.json"
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

    message: dict = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }
    if metadata is not None:
        message["metadata"] = metadata

    data["messages"].append(message)
    data["last_message"] = content[:100] if content else ""
    data["updated_at"] = datetime.now().isoformat()

    history_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_todo_manager_by_tid(thread_id: str):
    """根据 thread_id 获取 TODO 管理器"""
    from web.todo_manager import TodoManager

    return TodoManager(thread_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.web_server:app", host="0.0.0.0", port=8000, reload=True)
