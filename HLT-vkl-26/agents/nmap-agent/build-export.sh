#!/usr/bin/env sh
set -eu

IMAGE_NAME="${IMAGE_NAME:-hlt-nmap-agent}"
IMAGE_TAG="${IMAGE_TAG:-0.2.0}"
OUTPUT_FILE="${OUTPUT_FILE:-${IMAGE_NAME}-${IMAGE_TAG}.tar}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI was not found. Install Docker, start the engine, then retry." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker engine is not running. Start Docker, wait until it is ready, then retry." >&2
  exit 1
fi

docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
docker save "${IMAGE_NAME}:${IMAGE_TAG}" -o "${OUTPUT_FILE}"

if [ ! -f "${OUTPUT_FILE}" ]; then
  echo "Docker image export failed." >&2
  exit 1
fi

echo "Exported Docker image to ${OUTPUT_FILE}"
