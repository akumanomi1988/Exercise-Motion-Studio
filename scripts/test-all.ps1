$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$old = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $root 'src/motion_pipeline'
    $python = 'python'
    if (Test-Path (Join-Path $root '.venv/Scripts/python.exe')) { $python = Join-Path $root '.venv/Scripts/python.exe' }
    & $python -m compileall -q (Join-Path $root 'src/motion_pipeline/ems')
    if ($LASTEXITCODE -ne 0) { throw 'Compile check failed.' }
    & $python -m unittest discover -s (Join-Path $root 'tests/unit') -v
    if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }
    Write-Host 'Bootstrap tests passed. This is NOT a MoCap/GLB/QA gate.'
}
finally { $env:PYTHONPATH = $old }
