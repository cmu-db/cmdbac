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

def search_file_norecur(directory_name, file_name):
    for file in os.listdir(directory_name):
        if os.path.isfile(os.path.join(directory_name, file)) and file == file_name:
            return True
    return False

def search_dir(directory_name, query_name):
    for root, dirs, files in os.walk(directory_name):
        for _dir in dirs:
            if query_name in _dir:
                path = os.path.join(root, _dir)
                return path

def replace_file_regex(file, string_pattern, string):
    with open(file, "r+") as f:
        s = f.read()
        s = re.sub(string_pattern, string, s, flags=re.DOTALL)
        f.seek(0)
        f.write(s)
        f.truncate()
        f.close()

def replace_files_regex(directory_name, string_pattern, string):
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            replace_file_regex(os.path.join(root, file), string_pattern, string)

def unzip(zip_name, dir_name):
    command = 'unzip -o -qq ' + zip_name + ' -d ' + dir_name
    out = run_command(command)

def rm_dir(path):
    #if os.path.exists(path):
    #    shutil.rmtree(path)
    os.system('sudo rm -rf {}'.format(path))

def mk_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def chmod_dir(path):
    if os.path.exists(path):
        os.chmod(path, 0777)

def make_dir(path):
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

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
            except:
                pass
    return total_size
