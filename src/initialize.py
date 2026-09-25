
import os
import shutil
from flask import current_app as app


def Initialize():
    

    # Chemin absolu du dossier template
    src = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "init_template"
        )
    )

    dst = app.config_folder

    if os.path.exists(dst):
        print(
            "Configuration already exists: %s",
            dst
        )
        return

    if not os.path.isdir(src):
        raise FileNotFoundError(
            f"Template directory not found: {src}"
        )

    shutil.copytree(src, dst)

    print(
        "Configuration initialized: %s",
        dst
    )