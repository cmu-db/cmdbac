import sys
import urllib2
import subprocess
import traceback
import logging
import time
from string import Template
import os
import os.path
from bs4 import BeautifulSoup
import json
import shutil
import urlparse
import importlib
from run import run

logging.basicConfig(format='%(asctime)s %(message)s', filename='utils.log', level=logging.DEBUG)

utils_logger = logging.getLogger('utils')
utils_logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('utils.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
utils_logger.addHandler(fh)
utils_logger.addHandler(ch)

DOWNLOAD_URL_TEMPLATE = Template('https://github.com/${name}/archive/${sha}.zip')
HOMEPAGE_URL_TEMPLATE = Template('https://github.com/${name}')
API_COMMITS_URL = Template('https://api.github.com/repos/${name}/commits')
HOME_DIR = "/home/vagrant/"
SHARE_DIR = "/vagrant/"

class Utils:
    @staticmethod
    def none2empty(string):
        if string:
            return string
        else:
            return ""

def run_command(command):
    return run(command, timeout=1000)[1]
    #logging.getLogger('utils').debug('run command: ' + command)
    #p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #out, err = p.communicate()
    #logging.getLogger('utils').debug('output: ' + out)
    #logging.getLogger('utils').debug('stderr: ' +err)
    #return out


def download(attempt, zip_name):
    url = DOWNLOAD_URL_TEMPLATE.substitute(name=attempt.repo.name, sha=attempt.sha)
    response = query(url)
    zip_file = open(zip_name, 'wb')
    shutil.copyfileobj(response.fp, zip_file)
    zip_file.close()

def vagrant_run_command(command):
    vagrant_command = "vagrant ssh -c '" + command + "'"
    out = run_command(vagrant_command)
    return out

def to_vm_path(file_name):
    return os.path.join(SHARE_DIR, file_name)

def vagrant_pip_clear():
    command = "sudo rm -rf " + os.path.join(HOME_DIR, "pip/build/") + ' ' + os.path.join(HOME_DIR, ".local/")
    return vagrant_run_command(command)

def vagrant_pip_freeze():
    out = vagrant_run_command("pip freeze")
    out = out.strip().splitlines()
    out = [line for line in out if not ' ' in line and '==' in line]
    return out

def pip_rm_build():
    # pip will save meta data in build directory if install failed
    command = "sudo rm -rf " + os.path.join(HOME_DIR, "pip/build")
    return vagrant_run_command(command)

def vagrant_pip_install(names, is_file):
    command = "pip "
    
   # command_t = Template("pip ${proxy} install --user --build /home/vagrant/pip/build")
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = command + "--proxy " + proxy + ' '
    command = command + "install --user --build /home/vagrant/pip/build "
   #     command = command_t.substitute(proxy="--proxy " + proxy)
    #else:
    #    command = command_t.substitute(proxy='')
    if is_file:
        vm_name = to_vm_path(names)
        command = command + "-r " + vm_name
    else:
        for name in names:
            command = command + name.name + "==" + name.version + ' '
    out = vagrant_run_command(command)

    pip_rm_build()
    return out

       
def search_file(directory_name, file_name):
    result = []
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if file == file_name:
                path = os.path.join(root, file)
                if not os.path.islink(path):
                    result.append(path)
    #print result
    return result
#    command = "find " + directory_name + " -type f -wholename '*/" + file_name + "'"
#    out = run_command(command)
#    out = out.strip().splitlines()
#    return out

def unzip(zip_name, dir_name):
    command = 'unzip -o -qq ' + zip_name + ' -d ' + dir_name
    out = run_command(command)

def block_ports():
    pass

def get_latest_sha(repo):
    url = API_COMMITS_URL.substitute(name=repo.name)
    #url = HOMEPAGE_URL_TEMPLATE.substitute(name=repo.name)
    try:
        response = query(url)
    except Exception, ex:
        print Exception,":",ex
    data = json.load(response)
    print data[0]['sha']
    time.sleep(1) 
    return data[0]['sha']
    #soup = BeautifulSoup(response.read())
    #sha_block = soup.find(class_='sha-block')
    #sha = os.path.basename(sha_block.get('href'))
    #print sha
    #return sha

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

def vagrant_cd(path):
    return cd(to_vm_path(path))

def get_urls(path, type_name):
    if type_name == "Ruby on Rails":
        command = vagrant_cd(path) + " && bundle exec rake routes"
        output = vagrant_run_command(command).split()
        urls = [word for word in output if word.startswith('/')]
    elif type_name == "Django":
        dirname = os.path.dirname(path)
        sys.path.append(dirname)
        proj_name = os.path.basename(path)
        command = "python " + to_vm_path('get_urls.py') + ' ' + to_vm_path(dirname) + ' ' + proj_name
        out = vagrant_run_command(command)
        if ' ' in out:
            urls = []
        else:
            urls = out.splitlines()
    return urls

def unblock_ports():
    pass

def query(url):
    #print url
    logging.debug('query url: ' + url)
    request = urllib2.Request(url)
    #request.add_header('Authorization', 'token %s' % TOKEN)
    #while True:
    #try:
    response = urllib2.urlopen(request)
    header = response.info().dict;
    logging.getLogger('utils').debug('response info from: ' + url)
    logging.getLogger('utils').debug(header)
    return response
