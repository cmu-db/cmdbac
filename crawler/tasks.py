from __future__ import absolute_import
from django.utils import timezone

from celery import shared_task
from crawler.models import *
from datetime import datetime
import urllib2
import subprocess
import shutil
import json
import time
import re
from django.db import IntegrityError
import traceback
import subprocess
import pkgutil
from os.path import join
from pip.index import PackageFinder, Link
from pip.download import PipSession
from pip.req import InstallRequirement
from bs4 import BeautifulSoup
import urlparse
from string import Template

token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
sys_path = '/usr/local/lib/python2.7/dist-packages'

isCount = 0
isntCount = 0

def query(url):
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            print('response from: 'url)
        except urllib2.HTTPError as e:
            traceback.print_exc()
            time.sleep(5)
            continue
        return response

def isReusableApp(fullname):
    global isCount
    global isntCount
    url = 'https://api.github.com/search/code?q=setup.py+language:python+in:path+repo:' + fullname
    print url
    response = query(url)
    data = json.load(response)
    print data['total_count']
    try:
        if(data['total_count'] != 0):
            isCount += 1
            print 'is ' + str(isCount)
            return True
    except:
        print 'exception'
    isntCount += 1
    print 'isnt ' + str(isntCount)
    return False


def searchFile(repoName, fileName):
    url = 'https://api.github.com/search/code?q=' + fileName + '+in:path+repo:' + repoName
    response = query(url)
    data = json.load(response)
    path = ''
    for item in data['items']:
        if '/' + fileName in item['path']:
            path = item['path']
            print 'found path ' + path
    return path
            
def run_command(command):
    print command
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    print out
    return out
    #return iter(p.stdout.readline, b'')




def appendSettings(directory, settingsPath):
    with open(directory + settingsPath, "a") as settingsFile:
        settingsFile.write("SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'\n")
        settingsFile.write("ALLOWED_HOSTS = ['localhost', '127.0.0.1']\n")

def solveDependency(module_name):
    module = Module.objects.filter(name = module_name)
    package = Package.objects.filter(name in mdoules.package)
    pip_install(package.name, package.version, True)

def runserver(directory, pk, managePath):
    threshold = 10
    line = 'placeholder'
    #for time in range(threshold):
    command = 'vagrant ssh -c ' + "'python /vagrant/" + directory + managePath + " runserver > /vagrant/crawler/static/crawler/log/" + str(pk) + " 2>&1 & sleep 10'"
    run_command(command)
    logFile = open('./crawler/static/crawler/log/' + str(pk), 'r')
    lines = logFile.readlines()
    logFile.close
    print lines
    if len(lines) == 0:
        print "Success"
        return Result.objects.get(result="Success")
    line = lines[len(lines)-1]
    #if(line.startsWith('ImportError')):
    #    solveDependency(line.split[-1])
    #else:
    if line.startswith('ImportError'):
        print 'ImportError'
        return Result.objects.get(result='Fail: Missing Dependency')
    else:
        print 'Other Reason'
        return Result.objects.get(result='Fail: Other Reason')

def initApp(item):
    app = Application()
    app.repo_id = item['id']
    app.pushed_at = datetime.strptime(item['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
    app.url = item['url']
    app.status = Status.objects.get(status = 'Found')

    #app = Application(repo_id=id, pushed_at=pushed_at, url=url, status=Status.objects.get(status='found'))
    return app

def save(entry):
    try:
        entry.save()
    except:
        traceback.print_exc()

def processLibrary(item):
    app = initApp(item)
    app.app_type = Type.objects.get(app_type = 'Django: Library')
    save(app)


#def saveApplication(item, result):
#    id = item['id']
#    pushed_at = item['pushed_at']
#    url = item['url']
#    time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
#    repo = Application(repo_id=id, pushed_at=time, url=url, result=result)
#
#    try:
#        repo.save()
#        print result
#    except IntegrityError as e:
#        print(e.message)

def delete(directoryName):
    command = 'rm -rf ' + directoryName
    run_command(command)

def processApplication(item):

    app = initApp(item)
    app.app_type = Type.objects.get(app_type = 'Django: Application')

    fullname = item['full_name']
    requirementsPath = searchFile(fullname, 'requirements.txt')
    if requirementsPath:
        app.requirements_path = requirementsPath
    
    settingsPath = searchFile(fullname, 'settings.py')
    print settingsPath
    if settingsPath:
        app.settings_path = settingsPath
    
    managePath = searchFile(fullname, 'manage.py')
    if managePath:
        app.manage_path = managePath

    models_path = searchFile(fullname, 'models.py')
    if models_path:
        app.models_path = models_path

    save(app)

def process(response):
    data = json.load(response)
    for item in data['items']:
        url = 'https://api.github.com/search/code?q=setup.py+language:python+in:path+repo:' + item['full_name']
        response = query(url)
        data = json.load(response)
        if data['total_count']:
            processLibrary(item)
        else:
            processApplication(item)

#        if not isReusableApp(item['full_name']):
#            id = item['id']
#            pushed_at = item['pushed_at']
#            url = item['url']
#            time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
#            repo = Repository(repo_id=id, pushed_at=time, url=url)
#            try:
#                repo.save()
#            except IntegrityError as e:
#                print(e.message)

@shared_task
def run_crawler():
    date = datetime.now().strftime("%Y-%m-%d")
    date = datetime(2014,9,9).strftime("%Y-%m-%d")
    time = Application.objects.all().order_by("pushed_at")[0].pushed_at
    date = time.strftime("%Y-%m-%d")
    #stopTime = timezone.make_aware(datetime(2014, 1, 1), timezone.get_default_timezone())
    stopTime = datetime(2014, 1, 1)
    print type(stopTime)
    while True:
        url = 'https://api.github.com/search/repositories?q=django+language:python+pushed:<=' + date + '&sort=updated&order=desc'
        while True:
            response = query(url)
            process(response)

            header = response.info()
            match = re.search('<(.*)>; rel="next"', str(header))
            if match == None:
                break
            else:
                url = match.group(1)
        time = Application.objects.all().order_by("pushed_at")[0].pushed_at
        print type(time)
        
        if(time <= stopTime):
            return 'end'
        date = time.strftime("%Y-%m-%d")

def download(full_name):
    url = 'https://api.github.com/repos/' + full_name + '/tarball'
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    response = query(request)
    tarName = full_name + '.tar'
    tarFile = open(tarName, 'wb')
    shutil.copyfileobj(response.fp, tarFile)
    tarFile.close()
    subprocess.call(['tar', '-xf', tarName])
    command = "tar -tf " + tarName + " | grep -o '^[^/]\+' | sort -u"
    directory = ""
    name = run_command(command)
    directory = name.rstrip('\n')
    subprocess.call(['rm', tarName])
    return directory

def pip_freeze():
    out = run_command("vagrant ssh -c 'pip freeze'")
    out.rstrip().split('\n')
    out = [p for p in out if not v.startswith('#') ]
    return out

def exist(package):
    name, version = package.split('==')
    if len(Package.objects.filter(name=name, version=version)):
        return True
    else:
        return False

def createPackage(package, package_type):
    name, version = package.split('==')
    p = Package()
    p.package_type = package_type
    p.name = name
    p.version = version
    p.count = 1
    save(p)

def pip_uninstall(package_name):
    run_command("vagrant ssh -c 'sudo pip uninstall -y " + package_name + "'")

def pip_install(package_name, package_version, dep):
    if dep:
        command = "vagrant ssh -c 'sudo pip install " + package_name + '==' + package_version + "'"
    else:
        command = "vagrant ssh -c 'sudo pip install --no-deps " + package_name + '==' + package_version + "'"
    run_command(command)

def list_modules(path):
    out = run_command("vagrant ssh -c \"python -c \\\"import pkgutil; print '\\n'.join([name for _, name, _ in pkgutil.iter_modules(['" + join(sys_path, path) + "'])])\\\"\"")
    return set(out.split())

def list_modules_recur(modules):
    out = run_command("vagrant ssh -c 'python /vagrant/list_modules.py " + ' '.join(modules) + "'")
    return set(out.split())

def createModuleToPackageMapping(modules, base, package):
    print 'base:' + base
    print modules
    for module in modules:
        is_pkg = False
        name = ''
        if module.endswith('True'):
            name = module[:-4]
            is_pkg = True
        else:
            name = module[:-5]
            is_pkg = False
        newBase = join(base, name)
        full_name = newBase.replace('/', '.')
        m = Module()
        m.name = full_name
        m.package = package
        save(m)
        if is_pkg:
            createModuleToPackageMapping(list_modules(join(sys_path, newBase)), newBase, package)

def createPackageMapping(package):
    name, version = package.split('==')

    p = Package.objects.get(name=name, version=version)
    pip_uninstall(name)
    #old_modules = [name for _, name, _ in pkgutil.iter_modules()]
    old_modules = list_modules('')
    pip_install(name, version, False)
    new_modules = list_modules('')
    diff_modules = [x for x in new_modules if x not in old_modules]
    modules = list_modules_recur(diff_modules)
    for module in modules:
        m = Module()
        m.name = module
        m.package = p
# for some unkonw reason, django choose to update instead of insert. @see bug 'update not insert'
        save(m)
#        try:
#            m.save(force_insert=True)
#        except:
#            print 'module_name = ' + module
#            raise

def installRequirements(directory, requirementsPath, app_type):
    if app_type.app_type == 'Django: Application':

#        old_packages = pip_freeze()
        run_command("vagrant ssh -c 'sudo pip install -r /vagrant/" + directory + requirementsPath + "'")
#        new_packages = pip_freeze()
#        diff_packages = new_packages - old_packages
#        print diff_packages
#
#        for package in diff_packages:
#            if not exist(package):
#                createPackage(package, app_type)
#                createPackageMapping(package)
                
def count_line(directory, models_path):
    try:
        with open(directory + models_path) as f:
            for i, l in enumerate(f):
                pass
        return i + 1
    except:
        return 0

#@shared_task
#def run_deployer():
#    while True:
#        apps = Application.objects.filter(status=Status.objects.get(status='Found')).order_by('pk')
#        for app in apps:
#            #app = Application.objects.get(pk=pk)
#                
#            directoryName = download(app.url, app.pk)
#
#            if app.requirements_path != '':
#                installRequirements(directoryName, app.requirements_path, app.app_type)
#            if app.settings_path != '':
#                appendSettings(directoryName, app.settings_path)
#            if app.models_path != '':
#                app.model_size = count_line(directoryName, app.models_path)
#            else:
#                app.model_size = 0
#            if app.manage_path != '':
#                result = runserver(directoryName, app.pk, app.manage_path)
#            else:
#                result = Result.objects.get(result='Can Not Deploy')
#
#            app.result = result
#            app.status = Status.objects.get(status='Deployed')
#            save(app)
#
#            delete(directoryName)

def get_versions(package):
    host = "https://pypi.python.org/simple/"
    url = urlparse.urljoin(host, package)
    url = url + '/'
    session = PipSession()
    session.timeout = 15
    session.auth.prmpting = True
    pf = PackageFinder(find_links=[], index_urls=host, use_wheel=True, allow_external=[], allow_unverified=[], allow_all_external=False, allow_all_prereleases=False, process_dependency_links=False, session=session,)

    location = [Link(url, trusted=True)]
    req = InstallRequirement.from_line(package, None)
    versions = []
    for page in pf._get_pages(location, req):
        versions = versions + [version for _, _, version in pf._package_versions(page.links, package)]
    return versions

@shared_task
def run_package_crawler():
    url = "https://pypi.python.org/simple/"
    print url
    while True:
        #response = urllib2.urlopen(url)
        response = query(url)
        soup = BeautifulSoup(response.read())
        for link in soup.find_all("a"):
            package = link.get('href')
            try:
                versions = get_versions(package)
            except:
                traceback.print_exc()
                continue
            for version in versions:
                print package + "==" + version
                #package_type = Type.objects.get(app_type = 'Django: Library')
                Package.objects.get_or_create(package_type='Django', name=package, version=version)

def iter_names(module_name):
    try:
        module = __import__(module_id)
        for name in dir(module):
            print """----------------
            found name: """ + name
            Name.objects.get_or_create(name=module_name, module__id=module_id)
    except:
        traceback.print_exc()

def iter_modules_recur(package_id, modules, base):
    for module in modules:
        newBase = os.path.join(base, module[1])
        module_name = newBase.replace('/', '.')
        print """+++++++++++++++++++++++++++++
        found module: """ + module_name
        module = Module.objects.get_or_create(name=module_name, package__id=package_id)
        #iter_names(module.pk)
        if module[2]:
            iter_modules_recur(package_id, pkgutil.iter_modules([os.path.join(sys_path, newBase)]), newBase)

def create_mapping(package):
    print 'creating mapping for ' + package.name + '==' + package.version
    pip_uninstall(package.name, package.version)
    old_modules = iter_modules('')
    old_modules_name = [name for _, name, _ in old_modules]
    print 'old modules length = ' + str(len(old_modules_name))
    print old_modules_name
    pip_install(package.name, package.version, False)
    new_modules = iter_modules('')
    diff_modules = [x for x in new_modules if x[1] not in old_modules_name]
    diff_modules_name = [name for _, name, _ in diff_modules]
    print 'diff modules length = ' + str(len(diff_modules_name))
    print diff_modules_name
    if len(diff_modules):
        print 'found modules'
        iter_modules_recur(package.pk, diff_modules, '')
    else:
        print 'not found modules'
        Module.objects.get_or_create(name='no_modules_in_this_package', package__id=package.pk)

@shared_task
def run_package_deployer():
    old_packages = pip_freeze()
    while True:
        cursor = query(sql)
        results = cursor.fetchall()
        packages = Package.objects.exclude(pk__in=Module.objects.values_list('package', flat=True))
        for package in packages:
            try:
                recover_packages(old_packages)
            
        for row in results:
            try:
                recover_packages(old_packages)
                print """##############################################################################################
                processing """ + package.name + '==' + package.version
                if Module.objects.filter(package=package.pk).exist():
                    print 'crawled'
                    continue
                print 'old package length = ' + str(len(old_packages))
                print old_packages
                pip_install(package.name, package.version, True)
                new_packages = pip_freeze()
                print 'new package length = ' + str(len(new_packages))
                print new_packages

                diff_packages = new_packages - old_packages

                print 'diff package length = ' + str(len(diff_packages))
                print diff_packages

                if not len(diff_packages):
                    print 'install failed'
                    Module.objects.get_or_create(package=package.pk, name='cant_resolve_because_install_failed')
                    continue


                for package in diff_packages:
                    package_name, package_version = package.split("==")
                    print """*****************
                    processing """ + package_name + '==' + package_version
                    package, created = Package.objects.get_or_create(name=package_name, version=package_version)
                          
                    if created or not Module.objects.filter(package=package.pk).exist():
                        print 'package_id = ' + str(package.pk)
                        create_mapping(package)
            except:
                traceback.print_exc()
                print "Error: unable to fecth data"

def crawl_repo(url):
    while True:
        print url
        response = query(url)
        soup = BeautifulSoup(response.read())
        titles = soup.find_all(class_='title')
        for title in titles:
            full_name = title.contents[1].string
            Repository.objects.get_or_create(full_name=full_name, repo_type='Django')
            time.sleep(1)
        next_page = soup.find(class_='next_page')
        if not next_page or not next_page.has_attr('href'):
            break;
        url = github_host + next_page['href']

@shard_task
def run_repo_crawler():
    template = Template('https://github.com/search?utf8=%E2%9C%93&q=models.py+in%3Apath+filename%3Amodels.py+size%3A${size}&type=Code&ref=searchresults')
    github_host = 'https://github.com'
# model file less than min_size don't use database
    min_size = 60
# less then 1000 files larger than threshold_size
    threshold_size = 55000
    while True:
        for size in range(min_size, threshold_size):
            url = template.substitute(size=size)
            crawl_repo(url)
        url = template.substitute(size='>' + str(threshold_size))
        crawl_repo(url)

def search_file(directory_name, file_name):
    command = "find db-webcrawler -type f -wholename '*/" + file_name + "'"
    out = run_command(command)
    out.rstrip().split('\n')
    
    return out


@shard_task
def run_repo_deployer():
    download_url_template = Template('https://api.github.com/repos/${full_name}/tarball')
    while True:
        repos = Repository.objects.exclude(pk__in=Attempt.objects.values_list('repo', flat=True))
        for repo in repos:
            attempt = Attempt()
            attempt.repo = repo
            attempt.result = "Deploying"
            attempt.time= datetime.now()
            attempt.save()
            download_url = download_url_template.substitue(full_name=repo.full_name)
            directory_name = download(repo.full_name)
            setup = search_file(directory_name, 'setup.py')
            if len(setup):
                attempt.result = "Not an Application"
                attempt.log = str(setup)
                attempt.save()
                delete(directory_name)
                continue

            manage = search_file(directory_name, 'manage.py')
            if not len(manage):
                attempt.result = "Missing Required Files"
                attempt.log = "can't find manage.py"
                attempt.save()
                delete(directory_name)
                continue
            else if len(manage) != 1:
                attempt.result = "Duplicate Required Files"
                attempt.log = "find more than one manage.py"
                attempt.save()
                delete(directory_name)
                continue
            
            settings = search_file(directory_name, 'settings.py')
            if not len(settings):
                attempt.result = "Missing Required Files"
                attempt.log = "can't find settings.py"
                attempt.save()
                delete(directory_name)
                continue
            else if len(settings) != 1:
                attempt.result = "Duplicate Required Files"
                attempt.log = "find more than one settings.py"
                attempt.save()
                delete(directory_name)
                continue

            requirements = search_file(directory_name, 'requirements.txt')

            result, log, pkg_from_file, pkg_from_db = deploy(directory_name, manage[0], settings[0], requirements)
            attempt.result = result
            attempt.log = log
            attempt.save()
            
            for pkg in pkg_from_file:
                dependency = Dependency(attempt=attempt, package=pkg, source='File')
                dependency.save()
            for pkg in pkg_from_db:
                dependency = Dependency(attempt=attempt, package=pkg, source='Database')
                dependency.save()

            delete(directory_name)
