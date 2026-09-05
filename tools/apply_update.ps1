# Applique une mise a jour Chess Pro apres fermeture du jeu.
param(
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [Parameter(Mandatory = $true)][string]$StagingDir,
    [string]$ExeName = "ChessPro.exe",
    [int]$ParentPid = 0,
    [int]$WaitSeconds = 90
)

$ErrorActionPreference = "Stop"

function Wait-ForProcessExit {
    param([int]$Pid, [int]$TimeoutSec)
    if ($Pid -le 0) {
        Start-Sleep -Seconds 2
        return
    }
    $elapsed = 0
    while ($elapsed -lt $TimeoutSec) {
        $proc = Get-Process -Id $Pid -ErrorAction SilentlyContinue
        if (-not $proc) {
            return
        }
        Start-Sleep -Seconds 1
        $elapsed += 1
    }
}

Wait-ForProcessExit -Pid $ParentPid -TimeoutSec $WaitSeconds

$preserve = @("engines", "update_url.txt")
$stagingItems = Get-ChildItem -LiteralPath $StagingDir -Force

foreach ($item in $stagingItems) {
    if ($preserve -contains $item.Name) {
        continue
    }
    $target = Join-Path $InstallDir $item.Name
    if ($item.PSIsContainer) {
        if (Test-Path -LiteralPath $target) {
            robocopy $item.FullName $target /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
        } else {
            Copy-Item -LiteralPath $item.FullName -Destination $target -Recurse -Force
        }
    } else {
        Copy-Item -LiteralPath $item.FullName -Destination $target -Force
    }
}

Get-ChildItem -LiteralPath $InstallDir -Recurse -File | ForEach-Object {
    Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue
}

$exePath = Join-Path $InstallDir $ExeName
if (Test-Path -LiteralPath $exePath) {
    Start-Process -LiteralPath $exePath -WorkingDirectory $InstallDir
}
