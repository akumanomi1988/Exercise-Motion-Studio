# One-time acquisition of the versioned official MediaPipe task bundle.
# This script never uploads input data, modifies PATH or installs cloud services.
# The exact binary hash is verified before making the file available to EMS.
param(
    [string] $Destination = 'data\models\pose_landmarker_full.task'
)
$ErrorActionPreference = 'Stop'
$expected = '5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1'
$url = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task'
$root = Split-Path -Parent $PSScriptRoot
if (-not [IO.Path]::IsPathRooted($Destination)) {
    $Destination = Join-Path $root $Destination
}
$Destination = [IO.Path]::GetFullPath($Destination)
$dir = Split-Path -Parent $Destination
New-Item -Path $dir -ItemType Directory -Force | Out-Null
if (Test-Path $Destination) {
    $actual = (Get-FileHash -Path $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -eq $expected) {
        Write-Host "MediaPipe full pose bundle verified at $Destination"
        exit 0
    }
    throw "Existing file has unexpected SHA256: $Destination. Refusing overwrite."
}
$tmp = "$Destination.partial.$([Guid]::NewGuid().ToString('N'))"
try {
    Invoke-WebRequest -Uri $url -OutFile $tmp -MaximumRedirection 3
    $actual = (Get-FileHash -Path $tmp -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        throw "Downloaded model hash differs from pinned version (actual=$actual)."
    }
    Move-Item -Path $tmp -Destination $Destination
    Write-Host "Model downloaded and pinned SHA256 verified: $Destination"
    Write-Host "Upstream Apache-2.0 statement: https://github.com/google-ai-edge/mediapipe/issues/6306"
}
finally {
    if (Test-Path $tmp) { Remove-Item -Path $tmp -Force }
}
