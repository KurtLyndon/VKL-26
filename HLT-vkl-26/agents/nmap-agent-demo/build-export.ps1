$ErrorActionPreference = "Stop"

$ImageName = if ($env:IMAGE_NAME) { $env:IMAGE_NAME } else { "hlt-nmap-agent" }
$ImageTag = if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "0.2.0" }
$OutputFile = if ($env:OUTPUT_FILE) { $env:OUTPUT_FILE } else { "$ImageName-$ImageTag.tar" }

docker build -t "${ImageName}:${ImageTag}" .
docker save "${ImageName}:${ImageTag}" -o $OutputFile

Write-Host "Exported Docker image to $OutputFile"
