FROM ubuntu:18.04 AS base

WORKDIR /home/player/MyPlayer

# Installation des paquets système
RUN apt-get update && apt-get install -y \
    python3.8 \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libasound2 \
    gstreamer1.0-alsa \
    alsa-utils \
    libpulse0 \
    gstreamer1.0-pulseaudio \
    zlib1g-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev \
    libfribidi-dev libxcb1-dev \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur
RUN useradd -m -u 1000 player && \
    mkdir -p /home/player/MyPlayer

# Environnement Python
COPY venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV HOME=/home/player

# Configuration
COPY player/init_config_docker/ /home/player/MyPlayer/player/init_config_docker/
COPY player/libs /usr/lib/x86_64-linux-gnu/

RUN mkdir -p /home/player/.Player/logs && \
    chown -R player:player /home/player && \
    chmod -R 755 /home/player/.Player

USER player

COPY --chmod=755 /player/entrypoint.sh /player/entrypoint.sh
ENTRYPOINT ["/player/entrypoint.sh"]


###############################################################################
# Image de production
###############################################################################

FROM base AS release

COPY player/src/ /home/player/MyPlayer/player/src/

CMD ["/opt/venv/bin/python3","/home/player/MyPlayer/player/src/main.py","-c","/home/player/.Player/config/config-docker.ini"]


###############################################################################
# Image de développement
###############################################################################

FROM base AS debug

CMD ["/opt/venv/bin/python3","-m","debugpy","--listen","0.0.0.0:5678","--wait-for-client","/home/player/MyPlayer/player/src/main.py","-c","/home/player/.Player/config/config-docker.ini"]
