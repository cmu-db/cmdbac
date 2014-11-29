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

#class Constant():
ZIP_FILE = 'tmp.zip'
TMP_DIR = 'tmp_dir'
DOWNLOAD_URL_TEMPLATE = Template('https://github.com/${full_name}/archive/${sha}.zip')
HOMEPAGE_URL_TEMPLATE = Template('https://github.com/${full_name}')
API_COMMITS_URL = Template('https://api.github.com/repos/${full_name}/commits')
HOME_DIR = "/home/vagrant/"
SHARE_DIR = "/vagrant/"
# the github token
TOKEN = '5b3563b9b8c4b044530eeb363b633ac1c9535356'

def query(url):
    print url
    logging.debug('query url: ' + url)
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % TOKEN)
    while True:
        try:
            response = urllib2.urlopen(request)
            header = response.info().dict;
            #logging.getLogger('utils').debug('response info from: ' + url)
            #logging.getLogger('utils').debug(header)

        except:
            logging.getLogger('utils').debug(traceback.print_exc())
            time.sleep(5)
            continue
        return response

def run_command(command):
    logging.getLogger('utils').debug('run command: ' + command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    logging.getLogger('utils').debug('output: ' + out)
    logging.getLogger('utils').debug('stderr: ' +err)
    return out


def download(commit):
    url = DOWNLOAD_URL_TEMPLATE.substitute(full_name=commit.repo.full_name, sha=commit.sha)
    response = query(url)
    zip_file = open(ZIP_FILE, 'wb')
    shutil.copyfileobj(response.fp, zip_file)
    zip_file.close()

def vagrant_run_command(command):
    vagrant_command = "vagrant ssh -c '" + command + "'"
    out = run_command(vagrant_command)
    return out

def to_vm_file(file_name):
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
    command = "sudo rm -rf " + os.path.join(HOME_DIR, "pip/build")
    return vagrant_run_command(command)

def vagrant_pip_install(name, is_file):
    command = "pip "
    
   # command_t = Template("pip ${proxy} install --user --build /home/vagrant/pip/build")
    proxy = os.environ.get('http_proxy')
    if proxy:
        command = command + "--proxy " + proxy + ' '
   #     command = command_t.substitute(proxy="--proxy " + proxy)
    #else:
    #    command = command_t.substitute(proxy='')
    if is_file:
        vm_name = to_vm_file(name)
        command = command + "-r " + vm_name
    else:
        command = command + name.name + "==" + name.version
    out = vagrant_run_command(command)

    pip_rm_build()
    return out


def rewrite_settings(path, type_name):
    if type_name == "Django":
        settings = """
SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {
'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'db_webcrawler',
}
}
"""
        with open(path, "a") as my_file:
            my_file.write(settings)
    elif type_name == "Ruby on Rails":
        settings = """
development:
  adapter: sqlite3
  database: db/development.sqlite3
  pool: 5
  timeout: 5000

test:
  adapter: sqlite3
  database: db/test.sqlite3
  pool: 5
  timeout: 5000

production:
  adapter: sqlite3
  database: db/production.sqlite3
  pool: 5
  timeout: 5000
"""
        with open(os.path.join(path, 'config/database.yml'), "w") as my_file:
            my_file.write(settings)

        settings = """
gem 'sqlite3'
"""
        with open(os.path.join(path, 'Gemfile'), "a") as my_file:
            my_file.write(settings)



def install_requirements(requirement_files, repo_type):
    installed_requirements = []
    if requirement_files:
        vagrant_pip_clear()
        if repo_type.name == 'Django':
            old_packages = vagrant_pip_freeze()
            for requirement_file in requirement_files:
                out = vagrant_pip_install(requirement_file, True)
            new_packages = vagrant_pip_freeze()
            diff_packages = set(new_packages) - set(old_packages)
            for package in diff_packages:
                name, version = package.split('==')
                pkg, created = Package.objects.get_or_create(name=name, version=version, package_type=Type(name='Django'))
                installed_requirements.append(pkg)


#TODO: add these to main function
                #dep = Dependency()
                #dep.attempt = attempt
                #dep.package = obj
                #dep.source = Source(name='File')
                #dep.save()
                #obj.count = obj.count + 1
                #obj.save()
        elif repo_type.name == "Ruby on Rails":
#TODO: implement ruby on rails
            pass
    return installed_requirements

def search_file(directory_name, file_name):
    result = []
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if file == file_name:
                result.append(os.path.join(root, file))
    print result
    return result
#    command = "find " + directory_name + " -type f -wholename '*/" + file_name + "'"
#    out = run_command(command)
#    out = out.strip().splitlines()
#    return out

def unzip():
    command = 'unzip -qq ' + ZIP_FILE + ' -d ' + TMP_DIR
    out = run_command(command)
    return TMP_DIR

def vagrant_syncdb(manage_file):
    vm_manage_file = to_vm_file(manage_file)
    command = "python " + vm_manage_file + " syncdb --noinput"
    return vagrant_run_command(command) 
def vagrant_runserver(manage_file):
    vm_manage_file = to_vm_file(manage_file)
    command = "python " + vm_manage_file + " runserver > /vagrant/log 2>&1 & sleep 10"
    return vagrant_run_command(command)

def get_latest_sha(repo):
    url = API_COMMITS_URL.substitute(full_name=repo.full_name)
    #url = HOMEPAGE_URL_TEMPLATE.substitute(full_name=repo.full_name)
    print url
    response = query(url)
    data = json.load(response)
    print data[0]['sha']
    time.sleep(1) 
    return data[0]['sha']
    #soup = BeautifulSoup(response.read())
    #sha_block = soup.find(class_='sha-block')
    #sha = os.path.basename(sha_block.get('href'))
    #print sha
    #return sha

def mk_tmp_dir():
    mk_dir(TMP_DIR)

def rm_dir(path):
    shutil.rmtree(path)

def mk_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remake_tmp_dir():
    rm_dir(TMP_DIR)
    mk_dir(TMP_DIR)

def cd(path):
    return "cd "+ path

def vagrant_cd(path):
    return cd(to_vm_file(path))

def vagrant_bundle_install(path):
    command = vagrant_cd(path) + " && bundle install"
    return vagrant_run_command(command)

def vagrant_rake_db_create(path):
    command = vagrant_cd(path) + " && bundle exec rake db:migrate"
    return vagrant_run_command(command)

def vagrant_rails_server(path):
    command = vagrant_cd(path) + " && bundle exec rails server > /vagrant/log 2>&1 & sleep 10"
    return vagrant_run_command(command)
