import os
import shutil
from pathlib import Path
import paths
from flask import current_app as app


def get_xdg_path(variable, default):
    return Path(
        os.environ.get(variable, default)
    ).expanduser()


def create_directory(path):
    path.mkdir(parents=True, exist_ok=True)


def copy_template(src, dst):
    src = Path(src)
    dst = Path(dst)

    if not src.is_dir():
        raise FileNotFoundError(
            f"Template directory not found: {src}"
        )

    def copier_uniquement_si_absent(source, destination):
        if os.path.exists(destination):
            print(f"Ignoré (déjà présent) : {destination}")
            return

        shutil.copy2(source, destination)

    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        copy_function=copier_uniquement_si_absent
    )

    print(f"Initialized: {dst}")


def Initialize():

    # ---------------------------------------------------------
    # XDG base directories
    # ---------------------------------------------------------

    app.config_folder = paths.config_folder
    app.data_folder = paths.data_folder
    app.cache_folder = paths.cache_folder
    app.state_folder = paths.state_folder
    app.runtime_folder = paths.runtime_folder

    app.backup_folder = paths.backup_folder
    app.mediafiles_folder = paths.mediafiles_folder
    app.plugins_folder = paths.plugins_folder
    app.transcoded_folder = paths.transcoded_folder
    app.logs_folder = paths.logs_folder
    app.socket_path = paths.socket_path

    # ---------------------------------------------------------
    # Create directories
    # ---------------------------------------------------------

 

    create_directory(app.backup_folder)
    create_directory(app.cache_folder)
    create_directory(app.transcoded_folder)
    create_directory(app.state_folder)
    create_directory(app.runtime_folder)

    # ---------------------------------------------------------
    # Initialize configuration from template
    # ---------------------------------------------------------

    src = Path(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "init_template"
            )
        )
    )

    # Configuration
    copy_template(
        src / "config",
        app.config_folder
    )

    copy_template(
        src / "mediafiles",
        app.mediafiles_folder
    )

    copy_template(
        src / "plugins",
        app.plugins_folder
    )

    # État / logs
    copy_template(
        src / "logs",
        app.logs_folder
    )

