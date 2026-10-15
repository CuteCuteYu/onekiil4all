@echo off
rem ============================================================================
rem  onekiil4all - Windows stopper
rem
rem  Stops the dev server. It kills THREE kinds of leftovers:
rem    1) whatever process is LISTENING on the port, and
rem    2) any python process running this project's web.web_server
rem    3) uvicorn reloader ORPHAN workers (command line is only
rem       "--multiprocessing-fork ... spawn_main" - they hold the port
rem       while the owning PID display may point at a dead parent)
rem  Rules 2+3 matter because uvicorn's reloader can leave an ORPHANED
rem  worker behind - which is exactly why Ctrl+C sometimes appears to
rem  do nothing.
rem
rem  Usage:
rem    stop.bat              stop the server on port 8000
rem    stop.bat 8080         stop the server on a custom port
rem ============================================================================

set "PORT=%~1"
if not defined PORT set "PORT=8000"

echo [INFO] Stopping the server on port %PORT% ...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=%PORT%; $ids=@(); $ids+=(Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue | Select-Object -ExpandProperty OwningProcess); $ids+=(Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object { $_.CommandLine -like '*web.web_server*' -or $_.CommandLine -like '*spawn_main*' } | Select-Object -ExpandProperty ProcessId); $ids=@($ids | Where-Object { $_ -and $_ -ne $PID } | Sort-Object -Unique); if ($ids.Count -eq 0) { Write-Output '[INFO] nothing found - no process is using this port'; exit 0 }; foreach ($i in $ids) { try { Stop-Process -Id $i -Force -ErrorAction Stop; Write-Output ('[OK] killed PID ' + $i) } catch { Write-Output ('[WARN] PID ' + $i + ' : ' + $_.Exception.Message) } }; for ($n=0; $n -lt 10; $n++) { if (-not (Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue)) { break }; Start-Sleep -Milliseconds 500 }; if (Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue) { Write-Output ('[ERROR] port ' + $p + ' is still in use. Run this script as Administrator, or close the server window.'); exit 1 } else { Write-Output ('[OK] port ' + $p + ' is free - server stopped') }"

if errorlevel 1 pause
