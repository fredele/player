#!/bin/sh

set -e

SOURCE_DIR=/home/player/MyPlayer/player/init_config_docker
TARGET_DIR="$HOME/.Player"


if [ ! -d "$TARGET_DIR" ]; then
    echo "Init config in $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    cp -a "$SOURCE_DIR/." "$TARGET_DIR/"
fi


exec "$@"