@echo off
cd /d "%~dp0"
if exist "dist\ChessPro\JOUEZ-ICI.bat" (
  start "" "dist\ChessPro\JOUEZ-ICI.bat"
  exit /b 0
)
if exist "dist\ChessPro\ChessPro.exe" (
  start "" /D "dist\ChessPro" "dist\ChessPro\ChessPro.exe"
  exit /b 0
)
echo Lancement en mode developpement...
py -3.12 main.py
if errorlevel 1 python main.py
pause
