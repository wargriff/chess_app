# Debloque Chess Pro pour Windows Defender / SmartScreen (zone Internet).
param([switch]$NoLaunch)

$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Chess Pro - Installation Windows ===" -ForegroundColor Green

Get-ChildItem -LiteralPath $root -Recurse -File | ForEach-Object {
    Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue
}

$exe = Join-Path $root "ChessPro.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    Write-Host "ChessPro.exe introuvable dans $root" -ForegroundColor Red
    Read-Host "Appuyez sur Entree"
    exit 1
}

Unblock-File -LiteralPath $exe

# Verifie Visual C++ Redistributable 2015-2022 (x64)
$vcKey = "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
$vcOk = $false
try {
    if (Test-Path -LiteralPath $vcKey) {
        $installed = Get-ItemProperty -LiteralPath $vcKey -ErrorAction Stop
        if ($installed.Installed -eq 1) { $vcOk = $true }
    }
} catch {}

if (-not $vcOk) {
    Write-Host ""
    Write-Host "Visual C++ 2015-2022 (x64) non detecte." -ForegroundColor Yellow
    Write-Host "Requis si erreur 'configuration cote-a-cote' au lancement." -ForegroundColor Yellow
    $installVc = Read-Host "Telecharger et installer VC++ maintenant ? (O/n)"
    if ($installVc -ne "n" -and $installVc -ne "N") {
        $vcUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        $vcInstaller = Join-Path $env:TEMP "vc_redist.x64.exe"
        try {
            Write-Host "Telechargement VC++..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $vcUrl -OutFile $vcInstaller -UseBasicParsing
            Write-Host "Installation VC++ (fenetre peut s'ouvrir)..." -ForegroundColor Cyan
            Start-Process -FilePath $vcInstaller -ArgumentList "/install", "/quiet", "/norestart" -Wait
            Write-Host "VC++ installe." -ForegroundColor Green
        } catch {
            Write-Host "Echec installation VC++ : $_" -ForegroundColor Red
            Write-Host "Installez manuellement : $vcUrl" -ForegroundColor Yellow
        }
    }
}

if ($root -match "\\build\\ChessPro$") {
    Write-Host ""
    Write-Host "ATTENTION : vous etes dans build\ChessPro (dossier temporaire)." -ForegroundColor Red
    Write-Host "Utilisez plutot dist\ChessPro apres compilation." -ForegroundColor Red
}

# Exclusion Defender (necessite admin, optionnel)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if ($isAdmin) {
    try {
        Add-MpPreference -ExclusionPath $root -ErrorAction Stop
        Write-Host "Exclusion Windows Defender ajoutee pour :" $root -ForegroundColor Cyan
    } catch {
        Write-Host "Exclusion Defender non ajoutee (Defender desactive ou politique GPO)." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Pour une exclusion Defender complete, relance ce script en Administrateur." -ForegroundColor Yellow
}

Write-Host ""
$shortcut = Join-Path $root "Chess Pro.lnk"
if (-not (Test-Path -LiteralPath $shortcut)) {
    try {
        $ws = New-Object -ComObject WScript.Shell
        $lnk = $ws.CreateShortcut($shortcut)
        $lnk.TargetPath = $exe
        $lnk.WorkingDirectory = $root
        $lnk.IconLocation = "$exe,0"
        $lnk.Description = "Chess Pro"
        $lnk.Save()
        Write-Host "Raccourci cree : Chess Pro.lnk" -ForegroundColor Cyan
    } catch {
        Write-Host "Raccourci non cree (COM indisponible)." -ForegroundColor Yellow
    }
}

Write-Host "Fichiers debloques." -ForegroundColor Green
Write-Host "Lancez le jeu avec (Explorateur Windows) :" -ForegroundColor Green
Write-Host "  - JOUEZ-ICI.bat (recommande)" -ForegroundColor White
Write-Host "  - ChessPro.exe" -ForegroundColor White
Write-Host "  - Chess Pro.lnk" -ForegroundColor White
Write-Host "  (Les .vbs sont bloques sur certains PC — ne les utilisez pas)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Ne lancez pas les .bat depuis Cursor/VS Code (ils s'ouvrent en texte)." -ForegroundColor Yellow
Write-Host ""
Write-Host "Si SmartScreen affiche un avertissement :" -ForegroundColor White
Write-Host "  1. Cliquez sur 'Informations complementaires'" -ForegroundColor White
Write-Host "  2. Puis 'Executer quand meme'" -ForegroundColor White
Write-Host ""

if (-not $NoLaunch) {
    $launch = Read-Host "Lancer Chess Pro maintenant ? (O/n)"
    if ($launch -ne "n" -and $launch -ne "N") {
        Start-Process -LiteralPath $exe -WorkingDirectory $root
    }
}
