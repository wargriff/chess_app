@echo off
title Chess Pro - Reparation
cd /d "%~dp0"
python tools\reparer.py
if errorlevel 1 pause
exit /b %ERRORLEVEL%
