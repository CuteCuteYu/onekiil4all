#!/usr/bin/env bash
# ============================================================================
#  上古必斩必杀 - Linux / macOS 启动脚本
#
#  用法:
#    ./start.sh              (使用默认端口 8000)
#    ./start.sh 8080         (指定端口)
#
#  模型凭据来源（按优先级）:
#    1) 环境变量 ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY
#       （含 ANTHROPIC_BASE_URL、ANTHROPIC_MODEL，本脚本不会覆盖它们）
#    2) 项目根目录下的 .env 文件
#  两者都没有时会给出提示并退出。
# ============================================================================
set -e

# 切到脚本所在目录（项目根），这样从任何位置运行都正确
cd "$(dirname "$0")"

PORT="${1:-${PORT:-8000}}"
export PORT

echo "============================================================"
echo "  上古必斩必杀 - 启动中"
echo "  项目目录: $(pwd)"
echo "============================================================"

# ── 1. 检查 uv ────────────────────────────────────────────────
if ! command -v uv >/dev/null 2>&1; then
    echo "[错误] 未找到 uv（Python 包管理器）。"
    echo "       请先安装后重试:"
    echo "         curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "       文档: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# ── 2. 检查模型凭据 ───────────────────────────────────────────
if [ -z "${ANTHROPIC_AUTH_TOKEN:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    if [ -f ".env" ]; then
        echo "[信息] 未检测到环境变量，将使用项目根目录的 .env 配置。"
    else
        echo "[错误] 缺少模型凭据，请二选一:"
        echo
        echo "  方式一（推荐）导出环境变量后重试:"
        echo "    export ANTHROPIC_AUTH_TOKEN=你的真实token"
        echo "    export ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic"
        echo "    export ANTHROPIC_MODEL=GLM-5.3"
        echo
        echo "  方式二 在项目根目录创建 .env 文件（内容同上，去掉 export）"
        echo
        exit 1
    fi
fi

# 占位符自检：避免带着 dummy 之类占位符启动，导致 401 却看不出原因
case "${ANTHROPIC_AUTH_TOKEN:-}" in
    dummy*)
        echo "[错误] ANTHROPIC_AUTH_TOKEN 看起来是占位符（dummy...），会导致模型返回 401。"
        echo "       请先执行:  export ANTHROPIC_AUTH_TOKEN=你的真实token"
        exit 1
        ;;
esac

# ── 3. 首次运行时同步依赖 ─────────────────────────────────────
if [ ! -x ".venv/bin/python" ] && [ ! -f ".venv/Scripts/python.exe" ]; then
    echo "[信息] 首次运行，正在同步依赖（使用国内镜像，通常几秒）..."
    uv sync
fi

# ── 4. 启动服务 ───────────────────────────────────────────────
# 直接用 venv 里的解释器，不套 "uv run"：多一层包装进程时 Ctrl+C 可能传不进服务
if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"   # Git Bash on Windows
else
    echo "[错误] 未找到虚拟环境解释器，请先执行: uv sync"
    exit 1
fi

# 默认关闭热重载：uvicorn 的 reloader 会派生 worker 子进程，异常中断时可能留下
# 孤儿进程继续占着端口，导致服务停不掉。需要热重载请先 export RELOAD=1
export RELOAD="${RELOAD:-0}"

echo "[信息] 服务启动中，浏览器访问: http://localhost:${PORT}"
echo "[信息] 按 Ctrl+C 停止服务"
echo "[信息] 若 Ctrl+C 无效：执行 ./stop.sh，或直接关闭终端窗口"
echo "[信息] 热重载: ${RELOAD}（export RELOAD=1 可开启）"
echo

exec "$PYTHON" -m web.web_server
