@echo off
title Chess Pro - Mise a jour
cd /d "%~dp0"
python tools\mettre_a_jour.py
if errorlevel 1 pause
exit /b %ERRORLEVEL%
