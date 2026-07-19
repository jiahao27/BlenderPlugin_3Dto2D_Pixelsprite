$ErrorActionPreference = "SilentlyContinue"

function Show-CommandPath {
    param(
        [string]$Name
    )

    $items = Get-Command $Name -ErrorAction SilentlyContinue
    if ($items) {
        Write-Host "${Name}:"
        $items | ForEach-Object { Write-Host "  $($_.Source)" }
    } else {
        Write-Host "${Name}: not found in PATH"
    }
}

Show-CommandPath "python"
Show-CommandPath "git"
Show-CommandPath "blender"

$knownGit = @(
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\cmd\git.exe"
)

$knownBlenderRoots = @(
    "C:\Program Files\Blender Foundation",
    "$env:LOCALAPPDATA\Programs\Blender Foundation"
)

Write-Host ""
Write-Host "Known Git locations:"
$knownGit | Where-Object { Test-Path -LiteralPath $_ } | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "Known Blender locations:"
foreach ($root in $knownBlenderRoots) {
    if (Test-Path -LiteralPath $root) {
        Get-ChildItem -LiteralPath $root -Recurse -Filter "blender.exe" |
            ForEach-Object { Write-Host "  $($_.FullName)" }
    }
}
