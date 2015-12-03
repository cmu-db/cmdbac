import os
from os.path import expanduser

from run import run_command
from file import cd

HOME_DIR = expanduser('~')

def home_path(path):
    return os.path.join(HOME_DIR, path)

def configure_env(path):
    command = 'virtualenv {}'.format(path)
    return run_command(command)

def to_env(path):
    return '{} && {}'.format(cd(path), 'source bin/activate')

def pip_install(path, names, is_file, has_version = True):
    command = '{} && pip --no-cache-dir install'.format(to_env(path))
    
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = '{} --proxy {} '.format(command, proxy)
    if is_file:
        filename = home_path(names)
        command = '{} -r {}'.format(command, filename)
    else:
        for name in names:
            if has_version and name.version != None and name.version != '':
                command = '{} {}=={} '.format(command, name.name, name.version)
            elif name.name == 'django':
                command = '{} {}==1.8.4'.format(command, name.name)
            else:
                command = '{} {}'.format(command, name.name)
    out = run_command(command)

    return out

def pip_install_text(path, name):
    command = '{} && pip --no-cache-dir install'.format(to_env(path))
    
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = '{} --proxy {} '.format(command, proxy)
    command = '{} {} '.format(command, name)
    out = run_command(command)

    return out

def pip_freeze(path):
    out = run_command('{} && pip freeze'.format(to_env(path)))
    out = out[1].strip().splitlines()
    out = [line for line in out if not ' ' in line and '==' in line]
    return out
