@echo off
cd /d "%~dp0"
set "GAME=C:\Users\wargriff\Pycharm_Project_v 3.12\chess_app\dist\ChessPro\JOUEZ-ICI.bat"
if not exist "%GAME%" (
  echo Compilez d'abord : py -3.12 tools\build_exe.py
  pause
  exit /b 1
)
start "" "%GAME%"
