#!/bin/bash
cd /home/fredele/MyPlayer/player/

# Lance Docker Compose
docker compose -f mongodb.yaml up -d

# Lance Python (le chemin devient "./venv/bin/python3" car on a fait un "cd")
../venv/bin/python3 ./src/main.py
