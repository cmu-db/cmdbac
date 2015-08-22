import os
from os.path import expanduser
from run import run_command
from file import cd

HOME_DIR = expanduser('~')

def home_path(path):
    return os.path.join(HOME_DIR, path)

def pip_clear():
    command = 'sudo rm -rf {} {}'.format(home_path('pip/build/'), home_path('.local/'))
    return run_command(command)

def pip_freeze():
    out = run_command('pip freeze')
    out = out.strip().splitlines()
    out = [line for line in out if not ' ' in line and '==' in line]
    return out

def pip_rm_build():
    # pip will save meta data in build directory if install failed
    command = 'sudo rm -rf {}'.format(home_path('pip/build'))
    return run_command(command)

def pip_install(names, is_file):
    command = 'pip '
    
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = command + '--proxy ' + proxy + ' '
    command = command + 'install --user --build ' + home_path("pip/build")
    if is_file:
        filename = home_path(names)
        command = command + '-r ' + filename
    else:
        for name in names:
            command = command + name.name + '==' + name.version + ' '
    out = run_command(command)

    pip_rm_build()
    return out