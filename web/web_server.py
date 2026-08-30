"""
========================================
FastAPI Web Server - Web服务器模块
========================================
功能: 应用装配入口 - 路由注册、生命周期管理、静态资源服务
路由实现拆分在 web/api/ 包中，后台任务见 background_tasks.py
 作者: 上古必斩必杀
"""

# ═══════════════════════════════════════════════════════════════════════
# 导入标准库模块
# ═══════════════════════════════════════════════════════════════════════

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 确保项目根目录在 sys.path 中（热重载 multiprocessing spawn 时
# 可能丢失 cwd，导致顶层模块找不到）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ═══════════════════════════════════════════════════════════════════════
# 导入FastAPI和相关依赖
# ═══════════════════════════════════════════════════════════════════════
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ═══════════════════════════════════════════════════════════════════════
# 导入项目内部模块
# ═══════════════════════════════════════════════════════════════════════
from web.api.alert_api import router as alert_router
from web.api.canvas_api import router as canvas_router
from web.api.chat_api import router as chat_router
from web.api.history_api import router as history_router
from web.api.intelligence_api import router as intelligence_router
from web.api.meta_api import router as meta_router
from web.api.rss_api import router as rss_router
from web.api.session_api import router as session_router
from web.background_tasks import alert_checker, rss_checker
from web.intelligence.trends import shutdown_executor
from web.paths import STATIC_DIR
from web.sse import EventBroadcaster

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# FastAPI 生命周期管理
# ═══════════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI生命周期管理
    应用启动和关闭时的处理逻辑
    """
    logger.info("Web server started")

    alert_broadcaster: EventBroadcaster = app.state.alert_broadcaster
    rss_broadcaster: EventBroadcaster = app.state.rss_broadcaster

    background_tasks = [
        asyncio.create_task(alert_checker(alert_broadcaster)),
        asyncio.create_task(rss_checker(rss_broadcaster)),
    ]

    yield

    for task in background_tasks:
        task.cancel()
    # 限时等待任务退出，避免卡在执行中的抓取
    await asyncio.wait(background_tasks, timeout=3)
    shutdown_executor()

    logger.info("Web server stopped")


# ═══════════════════════════════════════════════════════════════════════
# FastAPI 应用初始化
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="上古必斩必杀 API",
    description="AI 聊天系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

# SSE 事件广播器（每个连接独立订阅，事件 fan-out）
app.state.alert_broadcaster = EventBroadcaster()
app.state.rss_broadcaster = EventBroadcaster()

# ═══════════════════════════════════════════════════════════════════════
# CORS中间件配置
# 默认允许所有来源（不携带凭据）；可用 CORS_ORIGINS 指定来源列表
# 注意 "*" 与 allow_credentials=True 的组合在浏览器侧无效，故互斥处理
# ═══════════════════════════════════════════════════════════════════════

_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
_allow_all = _cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════
# 静态文件服务与路由注册
# ═══════════════════════════════════════════════════════════════════════


class _NoCacheStaticFiles(StaticFiles):
    """开发用静态文件服务：禁用浏览器缓存，避免改前端代码后看不到效果"""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


# 挂载静态文件目录到 /static 路径
app.mount("/static", _NoCacheStaticFiles(directory=str(STATIC_DIR)), name="static")

# 注册API路由
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(history_router)
app.include_router(meta_router)
app.include_router(intelligence_router)
app.include_router(alert_router)
app.include_router(rss_router)
app.include_router(canvas_router)


@app.get("/")
async def index():
    """返回主页HTML文件"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/alert")
async def alert_page(keyword: str | None = None):
    """返回告警详情页面"""
    return FileResponse(STATIC_DIR / "alert.html")


# ═══════════════════════════════════════════════════════════════════════
# 主程序入口
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Windows 下强制 UTF-8 模式：默认 GBK 编码会让 deepagents 内置 read_file
    # 等工具读取 UTF-8 文件时抛 UnicodeDecodeError，导致 agent loop 中断。
    # 检测到非 UTF-8 模式时用 -X utf8 重新启动一次。
    if sys.platform == "win32" and not sys.flags.utf8_mode:
        os.execv(
            sys.executable,
            [sys.executable, "-X", "utf8", "-m", "web.web_server"],
        )

    import uvicorn

    # 默认只绑定本机回环地址；如需局域网访问设置 HOST=0.0.0.0
    # timeout_graceful_shutdown: 优雅关闭超时(秒)。SSE 长连接会让 reload 重载
    # 时旧 worker 永远等不到连接关闭而卡死, 加超时强制退出避免该问题
    uvicorn.run(
        "web.web_server:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
        timeout_graceful_shutdown=5,
    )
