import os
from run_command import run_command
from file import cd

def vagrant_run_command(command):
    vagrant_command = "vagrant ssh -c '" + command + "'"
    out = run_command(vagrant_command)
    return out

SHARE_DIR = "/vagrant/"

def vagrant_share_path(path):
    return os.path.join(SHARE_DIR, path)

def vagrant_cd(path):
    return "cd " + vagrant_share_path(path)

HOME_DIR = "/home/vagrant/"

def vagrant_home_path(path):
	return os.path.join(HOME_DIR, path)

def vagrant_pip_clear():
    command = "sudo rm -rf " + vagrant_home_path("pip/build/") + ' ' + vagrant_home_path(".local/")
    return vagrant_run_command(command)

def vagrant_pip_freeze():
    out = vagrant_run_command("pip freeze")
    out = out.strip().splitlines()
    out = [line for line in out if not ' ' in line and '==' in line]
    return out

def vagrant_pip_rm_build():
    # pip will save meta data in build directory if install failed
    command = "sudo rm -rf " + vagrant_home_path("pip/build")
    return vagrant_run_command(command)

def vagrant_pip_install(names, is_file):
    command = "pip "
    
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = command + "--proxy " + proxy + ' '
    command = command + "install --user --build " + vagrant_home_path("pip/build")
    if is_file:
        vm_name = to_vm_path(names)
        command = command + "-r " + vm_name
    else:
        for name in names:
            command = command + name.name + "==" + name.version + ' '
    out = vagrant_run_command(command)

    vagrant_pip_rm_build()
    return out

