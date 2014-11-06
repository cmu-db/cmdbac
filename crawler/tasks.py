#from __future__ import absolute_import
#from django.utils import timezone
#
#from celery import shared_task
#from crawler.models import *
#from datetime import datetime
#import urllib2
#import subprocess
#import shutil
#import json
#import time
#import re
#from django.db import IntegrityError
#import traceback
#import subprocess
#import pkgutil
#from os.path import join
#from pip.index import PackageFinder, Link
#from pip.download import PipSession
#from pip.req import InstallRequirement
#from bs4 import BeautifulSoup
#import urlparse
#from string import Template
#
#token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
#sys_path = '/usr/local/lib/python2.7/dist-packages'
#
#isCount = 0
#isntCount = 0
#
#def query(url):
#    request = urllib2.Request(url)
#    request.add_header('Authorization', 'token %s' % token)
#    while True:
#        try:
#            response = urllib2.urlopen(request)
#            print(url)
#        except urllib2.HTTPError as e:
#            #traceback.print_exc()
#            time.sleep(5)
#            continue
#        return response
#
#def isReusableApp(fullname):
#    global isCount
#    global isntCount
#    url = 'https://api.github.com/search/code?q=setup.py+language:python+in:path+repo:' + fullname
#    print url
#    response = query(url)
#    data = json.load(response)
#    print data['total_count']
#    try:
#        if(data['total_count'] != 0):
#            isCount += 1
#            print 'is ' + str(isCount)
#            return True
#    except:
#        print 'exception'
#    isntCount += 1
#    print 'isnt ' + str(isntCount)
#    return False
#
#
#def searchFile(repoName, fileName):
#    url = 'https://api.github.com/search/code?q=' + fileName + '+in:path+repo:' + repoName
#    response = query(url)
#    data = json.load(response)
#    path = ''
#    for item in data['items']:
#        if '/' + fileName in item['path']:
#            path = item['path']
#            print 'found path ' + path
#    return path
#            
#def run_command(command):
#    print command
#    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#    out, err = p.communicate()
#    print out
#    return out
#    #return iter(p.stdout.readline, b'')
#
#
#
#
#def appendSettings(directory, settingsPath):
#    with open(directory + settingsPath, "a") as settingsFile:
#        settingsFile.write("SECRET_KEY = 'abcdefghijklmnopqrstuvwxyz'\n")
#        settingsFile.write("ALLOWED_HOSTS = ['localhost', '127.0.0.1']\n")
#
#def solveDependency(module_name):
#    module = Module.objects.filter(name = module_name)
#    package = Package.objects.filter(name in mdoules.package)
#    pip_install(package.name, package.version, True)
#
#def runserver(directory, pk, managePath):
#    threshold = 10
#    line = 'placeholder'
#    #for time in range(threshold):
#    command = 'vagrant ssh -c ' + "'python /vagrant/" + directory + managePath + " runserver > /vagrant/crawler/static/crawler/log/" + str(pk) + " 2>&1 & sleep 10'"
#    run_command(command)
#    logFile = open('./crawler/static/crawler/log/' + str(pk), 'r')
#    lines = logFile.readlines()
#    logFile.close
#    print lines
#    if len(lines) == 0:
#        print "Success"
#        return Result.objects.get(result="Success")
#    line = lines[len(lines)-1]
#    #if(line.startsWith('ImportError')):
#    #    solveDependency(line.split[-1])
#    #else:
#    if line.startswith('ImportError'):
#        print 'ImportError'
#        return Result.objects.get(result='Fail: Missing Dependency')
#    else:
#        print 'Other Reason'
#        return Result.objects.get(result='Fail: Other Reason')
#
#def initApp(item):
#    app = Application()
#    app.repo_id = item['id']
#    app.pushed_at = datetime.strptime(item['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")
#    app.url = item['url']
#    app.status = Status.objects.get(status = 'Found')
#
#    #app = Application(repo_id=id, pushed_at=pushed_at, url=url, status=Status.objects.get(status='found'))
#    return app
#
#def save(entry):
#    try:
#        entry.save()
#    except:
#        traceback.print_exc()
#
#def processLibrary(item):
#    app = initApp(item)
#    app.app_type = Type.objects.get(app_type = 'Django: Library')
#    save(app)
#
#
##def saveApplication(item, result):
##    id = item['id']
##    pushed_at = item['pushed_at']
##    url = item['url']
##    time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
##    repo = Application(repo_id=id, pushed_at=time, url=url, result=result)
##
##    try:
##        repo.save()
##        print result
##    except IntegrityError as e:
##        print(e.message)
#
#def delete(directoryName):
#    command = 'rm -rf ' + directoryName
#    run_command(command)
#
#def processApplication(item):
#
#    app = initApp(item)
#    app.app_type = Type.objects.get(app_type = 'Django: Application')
#
#    fullname = item['full_name']
#    requirementsPath = searchFile(fullname, 'requirements.txt')
#    if requirementsPath:
#        app.requirements_path = requirementsPath
#    
#    settingsPath = searchFile(fullname, 'settings.py')
#    print settingsPath
#    if settingsPath:
#        app.settings_path = settingsPath
#    
#    managePath = searchFile(fullname, 'manage.py')
#    if managePath:
#        app.manage_path = managePath
#
#    models_path = searchFile(fullname, 'models.py')
#    if models_path:
#        app.models_path = models_path
#
#    save(app)
#
#def process(response):
#    data = json.load(response)
#    for item in data['items']:
#        url = 'https://api.github.com/search/code?q=setup.py+language:python+in:path+repo:' + item['full_name']
#        response = query(url)
#        data = json.load(response)
#        if data['total_count']:
#            processLibrary(item)
#        else:
#            processApplication(item)
#
##        if not isReusableApp(item['full_name']):
##            id = item['id']
##            pushed_at = item['pushed_at']
##            url = item['url']
##            time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
##            repo = Repository(repo_id=id, pushed_at=time, url=url)
##            try:
##                repo.save()
##            except IntegrityError as e:
##                print(e.message)
#
#@shared_task
#def run_crawler():
#    date = datetime.now().strftime("%Y-%m-%d")
#    date = datetime(2014,9,9).strftime("%Y-%m-%d")
#    time = Application.objects.all().order_by("pushed_at")[0].pushed_at
#    date = time.strftime("%Y-%m-%d")
#    #stopTime = timezone.make_aware(datetime(2014, 1, 1), timezone.get_default_timezone())
#    stopTime = datetime(2014, 1, 1)
#    print type(stopTime)
#    while True:
#        url = 'https://api.github.com/search/repositories?q=django+language:python+pushed:<=' + date + '&sort=updated&order=desc'
#        while True:
#            response = query(url)
#            process(response)
#
#            header = response.info()
#            match = re.search('<(.*)>; rel="next"', str(header))
#            if match == None:
#                break
#            else:
#                url = match.group(1)
#        time = Application.objects.all().order_by("pushed_at")[0].pushed_at
#        print type(time)
#        
#        if(time <= stopTime):
#            return 'end'
#        date = time.strftime("%Y-%m-%d")
#
#def download(url, pk):
#    request = urllib2.Request(url + '/tarball')
#    request.add_header('Authorization', 'token %s' % token)
#    response = urllib2.urlopen(request)
#    tarName = str(pk) + '.tar'
#    tarFile = open(tarName, 'wb')
#    shutil.copyfileobj(response.fp, tarFile)
#    tarFile.close()
#    subprocess.call(['tar', '-xf', tarName])
#    command = "tar -tf " + tarName + " | grep -o '^[^/]\+' | sort -u"
#    directory = ""
#    name = run_command(command)
#    directory = name.rstrip('\n') + '/'
#    #subprocess.call(['rm', tarName])
#    return directory
#
#def pip_freeze():
#    out = run_command("vagrant ssh -c 'pip freeze'")
#    return set(out.split())
#
#def exist(package):
#    name, version = package.split('==')
#    if len(Package.objects.filter(name=name, version=version)):
#        return True
#    else:
#        return False
#
#def createPackage(package, package_type):
#    name, version = package.split('==')
#    p = Package()
#    p.package_type = package_type
#    p.name = name
#    p.version = version
#    p.count = 1
#    save(p)
#
#def pip_uninstall(package_name):
#    run_command("vagrant ssh -c 'sudo pip uninstall -y " + package_name + "'")
#
#def pip_install(package_name, package_version, dep):
#    if dep:
#        command = "vagrant ssh -c 'sudo pip install " + package_name + '==' + package_version + "'"
#    else:
#        command = "vagrant ssh -c 'sudo pip install --no-deps " + package_name + '==' + package_version + "'"
#    run_command(command)
#
#def list_modules(path):
#    out = run_command("vagrant ssh -c \"python -c \\\"import pkgutil; print '\\n'.join([name for _, name, _ in pkgutil.iter_modules(['" + join(sys_path, path) + "'])])\\\"\"")
#    return set(out.split())
#
#def list_modules_recur(modules):
#    out = run_command("vagrant ssh -c 'python /vagrant/list_modules.py " + ' '.join(modules) + "'")
#    return set(out.split())
#
#def createModuleToPackageMapping(modules, base, package):
#    print 'base:' + base
#    print modules
#    for module in modules:
#        is_pkg = False
#        name = ''
#        if module.endswith('True'):
#            name = module[:-4]
#            is_pkg = True
#        else:
#            name = module[:-5]
#            is_pkg = False
#        newBase = join(base, name)
#        full_name = newBase.replace('/', '.')
#        m = Module()
#        m.name = full_name
#        m.package = package
#        save(m)
#        if is_pkg:
#            createModuleToPackageMapping(list_modules(join(sys_path, newBase)), newBase, package)
#
#def createPackageMapping(package):
#    name, version = package.split('==')
#
#    p = Package.objects.get(name=name, version=version)
#    pip_uninstall(name)
#    #old_modules = [name for _, name, _ in pkgutil.iter_modules()]
#    old_modules = list_modules('')
#    pip_install(name, version, False)
#    new_modules = list_modules('')
#    diff_modules = [x for x in new_modules if x not in old_modules]
#    modules = list_modules_recur(diff_modules)
#    for module in modules:
#        m = Module()
#        m.name = module
#        m.package = p
## for some unkonw reason, django choose to update instead of insert. @see bug 'update not insert'
#        save(m)
##        try:
##            m.save(force_insert=True)
##        except:
##            print 'module_name = ' + module
##            raise
#
#def installRequirements(directory, requirementsPath, app_type):
#    if app_type.app_type == 'Django: Application':
#
##        old_packages = pip_freeze()
#        run_command("vagrant ssh -c 'sudo pip install -r /vagrant/" + directory + requirementsPath + "'")
##        new_packages = pip_freeze()
##        diff_packages = new_packages - old_packages
##        print diff_packages
##
##        for package in diff_packages:
##            if not exist(package):
##                createPackage(package, app_type)
##                createPackageMapping(package)
#                
#def count_line(directory, models_path):
#    try:
#        with open(directory + models_path) as f:
#            for i, l in enumerate(f):
#                pass
#        return i + 1
#    except:
#        return 0
#
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
#
#@shared_task
#def run_crawler_2():
#    date = datetime.now().strftime("%Y-%m-%d")
#
#host = "https://pypi.python.org/simple/"
#
#def get_versions(package):
#    url = urlparse.urljoin(host, package)
#    url = url + '/'
#    session = PipSession()
#    session.timeout = 15
#    session.auth.prmpting = True
#    pf = PackageFinder(find_links=[], index_urls="https://pypi.python.org/simple/", use_wheel=True, allow_external=[], allow_unverified=[], allow_all_external=False, allow_all_prereleases=False, process_dependency_links=False, session=session,)
#
#    location = [Link(url, trusted=True)]
#    req = InstallRequirement.from_line(package, None)
#    versions = []
#    for page in pf._get_pages(location, req):
#        versions = versions + [version for _, _, version in pf._package_versions(page.links, package)]
#    return versions
#
#@shared_task
#def run_package_crawler():
#    url = "https://pypi.python.org/simple/"
#    print url
#    response = urllib2.urlopen(url)
#    soup = BeautifulSoup(response.read())
#
#    last = Package.objects.all().order_by("-name")[0].name
#    for link in soup.find_all("a"):
#        
#        package = link.get('href')
#        if package < last:
#            continue
#        
#        try:
#            versions = get_versions(package)
#        except:
#            continue
#        for version in versions:
#            print package + "==" + version
#            package_type = Type.objects.get(app_type = 'Django: Library')
#            Package.objects.get_or_create(package_type=package_type, name=package, version=version, count=1)
