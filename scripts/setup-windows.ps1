# Bootstrap: Python standard library only; does not install CUDA, Blender or FFmpeg.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.11+ not found; install it before proceeding.'
}
$python = 'python'
if (Get-Command py -ErrorAction SilentlyContinue) { $python = 'py' }
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    & $python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Unable to create Python virtual environment.' }
}
$env:PYTHONPATH = Join-Path $root 'src/motion_pipeline'
& '.\.venv\Scripts\python.exe' -m ems doctor
if ($LASTEXITCODE -ne 0) { throw 'CLI doctor failed.' }
Write-Host 'Bootstrap complete. This does not mean MoCap or render gates have passed.'
