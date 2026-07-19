param(
    [string]$BlenderPath = "E:\stream\steamapps\common\Blender\blender.exe"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CheckScript = Join-Path $ProjectRoot "scripts\check_addon_in_blender.py"

if (-not (Test-Path -LiteralPath $BlenderPath)) {
    throw "Blender executable not found: $BlenderPath"
}

& $BlenderPath --background --factory-startup --python $CheckScript
