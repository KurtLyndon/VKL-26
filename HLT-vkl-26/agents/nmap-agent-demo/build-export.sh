#!/usr/bin/env sh
set -eu

IMAGE_NAME="${IMAGE_NAME:-hlt-nmap-agent}"
IMAGE_TAG="${IMAGE_TAG:-0.2.0}"
OUTPUT_FILE="${OUTPUT_FILE:-${IMAGE_NAME}-${IMAGE_TAG}.tar}"

docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
docker save "${IMAGE_NAME}:${IMAGE_TAG}" -o "${OUTPUT_FILE}"

echo "Exported Docker image to ${OUTPUT_FILE}"
