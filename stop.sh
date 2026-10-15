#!/usr/bin/env bash
# ============================================================================
#  onekiil4all - Linux / macOS stopper
#
#  停止开发服务器。会同时处理：
#    1) 监听该端口的进程
#    2) 本项目 web.web_server 的服务进程
#  用于 Ctrl+C 无法停止服务时（例如 reloader 留下了孤儿 worker）。
#
#  用法:
#    ./stop.sh              停止 8000 端口的服务
#    ./stop.sh 8080         停止自定义端口的服务
# ============================================================================
set -e

PORT="${1:-${PORT:-8000}}"

echo "[信息] 正在停止端口 ${PORT} 上的服务 ..."

# 端口是否仍被监听（无法检测时按“未占用”处理）
port_busy() {
    if command -v lsof >/dev/null 2>&1; then
        if [ -n "$(lsof -t -i:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)" ]; then
            return 0
        fi
        return 1
    fi
    if command -v ss >/dev/null 2>&1; then
        if ss -ltnH "sport = :${PORT}" 2>/dev/null | grep -q .; then
            return 0
        fi
        return 1
    fi
    return 1
}

# ── 收集目标进程 ──────────────────────────────────────────────
PIDS=""

# 1) 监听该端口的进程
if command -v lsof >/dev/null 2>&1; then
    PIDS="${PIDS} $(lsof -t -i:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
elif command -v ss >/dev/null 2>&1; then
    PIDS="${PIDS} $(ss -lptnH "sport = :${PORT}" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 || true)"
elif command -v fuser >/dev/null 2>&1; then
    PIDS="${PIDS} $(fuser -n tcp "${PORT}" 2>/dev/null || true)"
fi

# 2) 兜底：本项目的服务进程 + uvicorn reloader 的孤儿 worker
#    （spawn worker 命令行只有 spawn_main，不含 web.web_server）
PIDS="${PIDS} $(pgrep -f 'web\.web_server' 2>/dev/null || true)"
PIDS="${PIDS} $(pgrep -f 'spawn_main' 2>/dev/null || true)"

TARGETS="$(printf '%s\n' ${PIDS} | tr -s ' ' '\n' | grep -E '^[0-9]+$' | sort -u | grep -vx "$$" || true)"

if [ -z "${TARGETS}" ]; then
    echo "[信息] 端口 ${PORT} 上没有监听进程，也没有本项目的服务进程。"
    exit 0
fi

echo "[信息] 终止进程: $(echo ${TARGETS} | tr '\n' ' ')"
# shellcheck disable=SC2086
kill -9 ${TARGETS} 2>/dev/null || true

# ── 确认端口已释放（最多等 5 秒）─────────────────────────────
i=0
while [ "${i}" -lt 10 ]; do
    if ! port_busy; then
        break
    fi
    sleep 0.5
    i=$((i + 1))
done

if port_busy; then
    echo "[错误] 端口 ${PORT} 仍被占用，请检查权限或手动处理。"
    exit 1
fi

echo "[完成] 端口 ${PORT} 已释放，服务已停止。"
