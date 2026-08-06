#!/bin/bash

set -e

echo "=== Installation des paquets système ==="
sudo apt-get update
sudo apt-get install -y python3.8 python3-pip python3-venv \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    gir1.2-gstreamer-1.0 gstreamer1.0-tools \
    gstreamer1.0-plugins-base gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly libpulse0 pulseaudio \
    zlib1g-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev libdiscid-dev

echo "=== Création du venv ==="
python3.8 -m venv venv

echo "=== Installation des paquets Python ==="

./venv/bin/pip3 install --upgrade pip setuptools wheel
./venv/bin/pip3 install -r requirements.txt


cp -r /coherence ~/MyPlayer/venv/lib/python3.8/site-packages
cp -r /bson ~/MyPlayer/venv/lib/python3.8/site-packages

