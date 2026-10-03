FROM ubuntu:18.04 AS base

WORKDIR /home/player/MyPlayer

# Installation des paquets système
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.8 \
    python3-pip \
    python3-gi \
    python3-gi-cairo \
    #gir1.2-gtk-3.0 \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libasound2 \
    gstreamer1.0-alsa \
    alsa-utils \
    libpulse0 \
    gstreamer1.0-pulseaudio \
    #zlib1g-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev \
    #libfreetype6-dev liblcms2-dev libwebp-dev libharfbuzz-dev \
    #libfribidi-dev libxcb1-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Création de l'utilisateur
RUN useradd -m -u 1000 player && \
    mkdir -p /home/player/MyPlayer

# Environnement Python
COPY venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV HOME=/home/player
ENV XDG_RUNTIME_DIR=/run/user/1000

# Configuration
COPY init_template/ /home/player/MyPlayer/init_template/
COPY libs /usr/lib/x86_64-linux-gnu/

RUN mkdir -p \
    /home/player/.config/player \
    /home/player/.local/share/player \
    /home/player/.cache/player \
    /home/player/.local/state/player

RUN chown -R player:player /home/player/.config/player \
                           /home/player/.local/share/player \
                           /home/player/.cache/player \
                           /home/player/.local/state/player



RUN mkdir -p /run/user/1000/player \
    && chown -R player:player /run/user/1000 \
    && chmod 700 /run/user/1000

USER player



###############################################################################
# Production Image
###############################################################################

FROM base AS release

COPY src/ /home/player/MyPlayer/src/

CMD ["/opt/venv/bin/python3","/home/player/MyPlayer/src/main.py"]


###############################################################################
# Dev. Image
###############################################################################

FROM base AS debug

CMD ["/opt/venv/bin/python3","-m","debugpy","--listen","0.0.0.0:5678","--wait-for-client","/home/player/MyPlayer/src/main.py","-c","/home/player/.Player/config/config-docker.ini"]
