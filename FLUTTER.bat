@echo off
cd /d "%~dp0"
title Chess Pro D4 — Flutter

echo ========================================
echo   CHESS PRO D4 — Lancement
echo ========================================
echo.

echo [1/2] Backend API (port 3848)...
netsh advfirewall firewall delete rule name="Chess Pro D4 3848" >nul 2>&1
netsh advfirewall firewall add rule name="Chess Pro D4 3848" dir=in action=allow protocol=TCP localport=3848 >nul 2>&1
start "Chess Pro D4 Backend" /MIN cmd /c "py -3.12 scripts\run_backend.py || python scripts\run_backend.py"

set /a tries=0
:wait_backend
set /a tries+=1
if %tries% GTR 45 (
  echo Backend lent — Flutter reessayera le health check.
  goto run_flutter
)
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri http://127.0.0.1:3848/health -UseBasicParsing -TimeoutSec 1; if ($r.Content -match 'Chess Pro D4' -and $r.Content -match '\"ok\"\s*:\s*true') { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto wait_backend
)
echo Backend Chess Pro D4 OK — http://127.0.0.1:3848/

:run_flutter
echo [2/2] Flutter Windows...
cd frontend\flutter_app
flutter run -d windows
pause
