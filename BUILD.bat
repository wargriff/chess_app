@echo off
cd /d "%~dp0"
title Chess Pro D4 — Build
echo === Verification dependances ===
where py >nul 2>&1 && set PY=py -3.12 || set PY=python
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Echec installation dependances
  pause
  exit /b 1
)
echo === Tests ===
%PY% scripts\test_all.py
if errorlevel 1 (
  echo Les tests ont echoue — build annule
  pause
  exit /b 1
)
echo === Build executable ===
%PY% tools\build_exe.py
if errorlevel 1 (
  echo Echec du build
  pause
  exit /b 1
)
echo.
echo Build OK : dist\ChessPro\ChessPro.exe
echo Lancez LANCER.bat pour demarrer.
pause
