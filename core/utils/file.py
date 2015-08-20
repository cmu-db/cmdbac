import os
import shutil
from run_command import run_command

def search_file(directory_name, file_name):
    result = []
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if file == file_name:
                path = os.path.join(root, file)
                if not os.path.islink(path):
                    result.append(path)
    return result

def unzip(zip_name, dir_name):
    command = 'unzip -o -qq ' + zip_name + ' -d ' + dir_name
    out = run_command(command)

def rm_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def mk_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remake_dir(path):
    rm_dir(path)
    mk_dir(path)

def cd(path):
    return "cd "+ path
