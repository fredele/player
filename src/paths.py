# paths.py

from pathlib import Path
import os


APP_NAME = "player"

config_folder = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / APP_NAME

data_folder = Path(
    os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
) / APP_NAME

cache_folder = Path(
    os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
) / APP_NAME

state_folder = Path(
    os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
) / APP_NAME

runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
if runtime_dir:
    runtime_folder = Path(runtime_dir) / APP_NAME
else:
    runtime_folder = Path("/run") / APP_NAME


# Sous-répertoires connus

backup_folder = data_folder / "backups"
mediafiles_folder = data_folder / "mediafiles"
plugins_folder = data_folder / "plugins"
transcoded_folder = cache_folder / "transcoded"
logs_folder = state_folder / "logs"
socket_path = runtime_folder / "scan.sock"