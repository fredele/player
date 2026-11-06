
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libasound2 \
    libpulse0 \
    && rm -rf /var/lib/apt/lists/*

# CamillaDSP : moteur audio avec prise en charge PulseAudio
RUN curl -fL \
    https://github.com/HEnquist/camilladsp/releases/download/v4.1.3/camilladsp-linux-pulseaudio-amd64.tar.gz \
    -o /tmp/camilladsp.tar.gz \
    && tar -xzf /tmp/camilladsp.tar.gz -C /tmp \
    && install -m 0755 /tmp/camilladsp /usr/local/bin/camilladsp \
    && rm /tmp/camilladsp.tar.gz /tmp/camilladsp

# CamillaGUI : serveur et interface Web
RUN curl -fL \
    https://github.com/HEnquist/camillagui-backend/releases/latest/download/bundle_linux_amd64.tar.gz \
    -o /tmp/camillagui.tar.gz \
    && tar -xzf /tmp/camillagui.tar.gz -C /opt \
    && rm /tmp/camillagui.tar.gz \
    && chmod +x /opt/camillagui_backend/camillagui_backend



RUN useradd -m -u 1000 player

# Préparation du répertoire d'exécution et création du Pipe pour CamillaDSP
RUN mkdir -p /run/user/1000/player \
    && mkfifo /run/user/1000/player/camilla_pipe \
    && chown -R player:player /run/user/1000 \
    && chmod 700 /run/user/1000

    
RUN mkdir -p /home/player/camilladsp/configs \
             /home/player/camilladsp/coeffs \
    && chown -R player:player /home/player/camilladsp
    


RUN find /opt/camillagui_backend -type f \
    \( -name 'camillagui.yml' -o -name '*.yml' -o -name '*.yaml' \) \
    -print

#COPY roc-send /usr/local/bin/roc-send
#RUN chmod 755 /usr/local/bin/roc-send

        
USER player
WORKDIR /config

