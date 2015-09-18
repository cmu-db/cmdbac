import os
import shutil
import re

from run import run_command

def search_file(directory_name, file_name):
    result = []
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if file == file_name:
                path = os.path.join(root, file)
                if not os.path.islink(path):
                    result.append(path)
    return result

def search_file_regex(directory_name, file_name_pattern):
    result = []
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if re.search(file_name_pattern, file):
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

def chmod_dir(path):
    if os.path.exists(path):
        os.chmod(path, 0777)

def remake_dir(path):
    rm_dir(path)
    mk_dir(path)
    chmod_dir(path)

def cd(path):
    return "cd "+ path

def rename_file(old_file, new_file):
    return run_command('mv {} {}'.format(
        old_file,
        new_file))

def copy_file(old_file, new_file):
    shutil.copy2(old_file, new_file)

def remove_file(path):
    try:
        os.remove(path)
    except:
        pass
