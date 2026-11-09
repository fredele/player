#!/bin/bash

# Génération de fichiers stéréo 10 secondes avec SoX
# Fréquences : 200, 400, 800, 1600, 3200, 6400 Hz
# Versions : gauche seule, droite seule, les deux canaux

DURATION=10
RATE=44100
VOLUME=0.5          # volume raisonnable (évite le clipping)
FREQS=(200 400 800 1600 3200 6400)

# Création du dossier de sortie
mkdir -p tones
cd tones

for f in "${FREQS[@]}"; do
    echo "Génération des fichiers pour ${f} Hz..."

    # Canal gauche uniquement
    sox -n -r $RATE -c 2 -b 16 "left_${f}Hz.wav" \
        synth $DURATION sine $f vol $VOLUME remix 1 0

    # Canal droit uniquement
    sox -n -r $RATE -c 2 -b 16 "right_${f}Hz.wav" \
        synth $DURATION sine $f vol $VOLUME remix 0 1

    # Les deux canaux (stéréo)
    sox -n -r $RATE -c 2 -b 16 "stereo_${f}Hz.wav" \
        synth $DURATION sine $f vol $VOLUME remix 1 1
done

echo
echo "Terminé ! Fichiers générés dans le dossier ./tones/"
ls -1
