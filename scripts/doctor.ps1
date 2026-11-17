$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$old = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $root 'src/motion_pipeline'
    $python = 'python'
    if (Test-Path (Join-Path $root '.venv/Scripts/python.exe')) { $python = Join-Path $root '.venv/Scripts/python.exe' }
    & $python -m ems doctor
    if ($LASTEXITCODE -ne 0) { throw 'Doctor command failed.' }
}
finally { $env:PYTHONPATH = $old }
