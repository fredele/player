import os
import shutil

def create_folder(f):
    # Create target Directory if don't exist
    if not os.path.exists(f):
        os.mkdir(f)

def create_data():
    src = os.path.abspath(os.path.join('..', 'init_config'))
    dst = os.path.join(os.getenv("HOME"), '.Player/config')

    try:
        shutil.copytree(src, dst)
    except Exception as e:
        print("COPY PLUGINS ERROR:", e)
        pass # Tree already exists

    src = os.path.abspath(os.path.join('..', 'init_plugins'))
    dst = os.path.join(os.getenv("HOME"), '.Player/plugins')

    try:
        mongolock = os.path.join(os.getenv("HOME"), '.Player/database/mongod.lock')
        os.remove(mongolock)
    except:
        pass #No mongo.lock file
    try:
        shutil.copytree(src, dst)
    except Exception as e:
        print("COPY PLUGINS ERROR:", e)
        pass # Tree already exists

# Create Folders ...
p = os.path.join(os.getenv("HOME"), '.Player')
create_folder(p)
p = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles')
create_folder(p)
# Copy init_data
create_data()
p = os.path.join(os.getenv("HOME"), '.Player', 'database')
create_folder(p)


p = os.path.join(os.getenv("HOME"), '.Player', 'backups')
create_folder(p)
p = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', 'Music')
create_folder(p)
p = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', 'Podcasts')
create_folder(p)
p = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', 'Playlists')
create_folder(p)
p = os.path.join(os.getenv("HOME"), '.Player', 'mediafiles', 'Radios')
create_folder(p)
