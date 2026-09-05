@echo off
title Chess Pro - Installation des prerequis
cd /d "%~dp0"
echo.
echo ========================================
echo   Chess Pro - Prerequis Windows
echo ========================================
echo.

echo [1/3] Deblocage des fichiers...
powershell -NoProfile -Command "Get-ChildItem -LiteralPath '%~dp0' -Recurse -File | ForEach-Object { Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue }"
echo OK.

echo.
echo [2/3] Visual C++ 2015-2022 (x64)...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed 2>nul | find "0x1" >nul
if %errorlevel%==0 (
    echo VC++ deja installe.
) else (
    echo Telechargement et installation VC++...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TEMP%\vc_redist.x64.exe' -UseBasicParsing"
    if exist "%TEMP%\vc_redist.x64.exe" (
        "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
        echo VC++ installe.
    ) else (
        echo Echec telechargement. Installez manuellement :
        echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    )
)

echo.
echo [3/3] Raccourcis...
if not exist "%~dp0Chess Pro.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" -NoLaunch
)

echo.
echo ========================================
echo   Pret ! Lancez JOUEZ-ICI.bat ou ChessPro.exe
echo ========================================
echo.
pause
