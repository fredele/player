import os

def isfile_insensitive(path):
    directory, filename = os.path.split(path)
    p = [os.path.split(f)[1] for f in os.listdir(directory)]
    if os.path.split(path)[1] in p :
        return True
    else:
        return False