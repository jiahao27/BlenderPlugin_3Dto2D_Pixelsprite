param(
    [string]$BlenderPath = "E:\stream\steamapps\common\Blender\blender.exe"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$SmokeScript = Join-Path $ProjectRoot "scripts\smoke_test_pixel_tools.py"

if (-not (Test-Path -LiteralPath $BlenderPath)) {
    throw "Blender executable not found: $BlenderPath"
}

& $BlenderPath --background --factory-startup --python $SmokeScript
