#!/bin/bash
set -e

HOME_DIR="$HOME"

docker rm -f myplayer 2>/dev/null || true

docker run -d \
    --name myplayer \
    --network host \
    -v /mnt/Disque_1/Music:/mnt/Disque_1/Music \
    -v /mnt/Disque_2/Music:/mnt/Disque_2/Music \
    -v /mnt/Disque_1/DB_Player/database:/data/db \
    -v "$HOME_DIR/.Player:/home/player/.Player" \
    -e PULSE_SERVER="unix:${XDG_RUNTIME_DIR}/pulse/native" \
    -v "${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native" \
    -v "$HOME_DIR/.config/pulse/cookie:/root/.config/pulse/cookie" \
    --group-add "$(getent group audio | cut -d: -f3)" \
    myplayer
