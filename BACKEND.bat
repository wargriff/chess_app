@echo off
cd /d "%~dp0"
title Chess Pro D4 — Backend (3848)
echo.
echo  Chess Pro D4 API  —  http://127.0.0.1:3848/
echo  Health : http://127.0.0.1:3848/health
echo.
REM Pare-feu : autoriser le port pour le telephone sur le meme Wi-Fi
netsh advfirewall firewall delete rule name="Chess Pro D4 3848" >nul 2>&1
netsh advfirewall firewall add rule name="Chess Pro D4 3848" dir=in action=allow protocol=TCP localport=3848 >nul 2>&1
py -3.12 -c "import fastapi,uvicorn,chess; print('deps OK')" 2>nul
if errorlevel 1 (
  echo [ERREUR] Dependances manquantes. Installez:
  echo   py -3.12 -m pip install fastapi "uvicorn[standard]" python-chess pydantic
  pause
  exit /b 1
)
py -3.12 scripts\run_backend.py
if errorlevel 1 (
  echo.
  echo [ERREUR] Backend arrete avec une erreur.
  python scripts\run_backend.py
)
pause
