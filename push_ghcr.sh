#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-myplayer}"
TARGET_IMAGE="${2:-ghcr.io/fredele/myplayer:latest}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [source_image] [target_image]"
  echo "Example: $0 myplayer ghcr.io/fredele/myplayer:latest"
  exit 0
fi

echo "Tagging ${IMAGE_NAME} -> ${TARGET_IMAGE}"
docker tag "${IMAGE_NAME}" "${TARGET_IMAGE}"
echo "Pushing ${TARGET_IMAGE}"
docker push "${TARGET_IMAGE}"

