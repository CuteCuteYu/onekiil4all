@echo off
rem ============================================================================
rem  onekiil4all - Windows launcher
rem
rem  NOTE: all messages here are ASCII on purpose. Non-ASCII text inside a .bat
rem  file is decoded with the active Windows code page and gets garbled (or even
rem  executed as a command) on some systems. Chinese docs live in README.md.
rem
rem  Usage:
rem    double-click            use default port 8000
rem    start.bat 8080          use a custom port
rem
rem  Model credentials are taken from (in order):
rem    1) environment variables ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY
rem       (plus optional ANTHROPIC_BASE_URL / ANTHROPIC_MODEL)
rem       These are never overwritten by this script.
rem    2) the .env file in the project root
rem ============================================================================

rem Move to this script's directory (project root) so it works from anywhere
cd /d "%~dp0"

rem Optional port argument:  start.bat 8080
if not "%~1"=="" set "PORT=%~1"
if not defined PORT set "PORT=8000"

echo ============================================================
echo   onekiil4all - starting
echo   project: %CD%
echo ============================================================

rem ── 1. check uv ─────────────────────────────────────────────────────────────
where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] "uv" was not found ^(Python package manager^).
    echo         Install it first:
    echo           powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"
    echo         Docs: https://docs.astral.sh/uv/getting-started/installation/
    echo.
    pause
    exit /b 1
)

rem ── 2. check model credentials ──────────────────────────────────────────────
if "%ANTHROPIC_AUTH_TOKEN%%ANTHROPIC_API_KEY%"=="" (
    if exist ".env" (
        echo [INFO] No ANTHROPIC_* environment variable found - using .env
    ) else (
        echo [ERROR] No model credentials found. Pick one of the two options:
        echo.
        echo   Option 1 ^(recommended^) - set user environment variables,
        echo   then reopen the terminal and run this script again:
        echo       setx ANTHROPIC_AUTH_TOKEN "your-real-token"
        echo       setx ANTHROPIC_BASE_URL   "https://open.bigmodel.cn/api/anthropic"
        echo       setx ANTHROPIC_MODEL      "GLM-5.3"
        echo.
        echo   Option 2 - create a file named .env in the project root with:
        echo       ANTHROPIC_AUTH_TOKEN=your-real-token
        echo       ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
        echo       ANTHROPIC_MODEL=GLM-5.3
        echo.
        echo   See README.md for details.
        echo.
        pause
        exit /b 1
    )
)

rem Placeholder self-check: starting with a dummy token gives HTTP 401 and the
rem agent stays silent, which is hard to diagnose - fail fast with a hint.
set "TOKCHK=%ANTHROPIC_AUTH_TOKEN%"
if /i "%TOKCHK:~0,5%"=="dummy" (
    echo [ERROR] ANTHROPIC_AUTH_TOKEN looks like a placeholder ^(dummy...^).
    echo         That causes HTTP 401 and the agent will not answer.
    echo         Fix it in this window, then re-run:
    echo           set ANTHROPIC_AUTH_TOKEN=your-real-token
    echo.
    pause
    exit /b 1
)

rem ── 3. first run: sync dependencies ─────────────────────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] First run - syncing dependencies ...
    uv sync
    if errorlevel 1 (
        echo [ERROR] Dependency sync failed. Check your network and retry.
        pause
        exit /b 1
    )
)

rem ── 4. start the server ─────────────────────────────────────────────────────
rem Run the venv Python DIRECTLY instead of going through "uv run": the extra
rem wrapper process on Windows can swallow Ctrl+C, so the server cannot be stopped.
set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo [ERROR] %PYTHON% not found. Run "uv sync" first.
    pause
    exit /b 1
)

rem Default to NO hot reload here: uvicorn's reloader spawns a child worker and on
rem Windows that worker can survive as an ORPHAN (still holding the port) when the
rem console is interrupted - then the server cannot be stopped at all.
rem Set RELOAD=1 before running this script to enable hot reload again.
if not defined RELOAD set "RELOAD=0"

echo [INFO] Starting server - open http://localhost:%PORT%
echo [INFO] Press Ctrl+C to stop.
echo        If Ctrl+C does not work: run stop.bat in this folder, or close this window.
echo        Hot reload: %RELOAD%  ^(set RELOAD=1 to enable^)
echo.

"%PYTHON%" -m web.web_server

if errorlevel 1 (
    echo.
    echo [ERROR] Server exited with an error - see the log above.
    pause
)
