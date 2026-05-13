$ErrorActionPreference = "Stop"

$ImageName = if ($env:IMAGE_NAME) { $env:IMAGE_NAME } else { "hlt-nmap-agent" }
$ImageTag = if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "0.2.0" }
$OutputFile = if ($env:OUTPUT_FILE) { $env:OUTPUT_FILE } else { "$ImageName-$ImageTag.tar" }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found. Install Docker Desktop, start it, then open a new PowerShell session."
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker engine is not running. Start Docker Desktop, wait until it is ready, then retry."
}

docker build -t "${ImageName}:${ImageTag}" .
if ($LASTEXITCODE -ne 0) {
    throw "Docker build failed."
}

docker save "${ImageName}:${ImageTag}" -o $OutputFile
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $OutputFile)) {
    throw "Docker image export failed."
}

Write-Host "Exported Docker image to $OutputFile"
