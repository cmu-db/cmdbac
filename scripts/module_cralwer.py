import MySQLdb
import os.path
import sys
import pkgutil
import traceback
import subprocess

sys_path = '/home/fangyug/ENV/local/lib/python2.7/site-packages'

db = MySQLdb.connect("localhost", "", "", "test")

def query(sql):
    global db
    print sql
    try:
        cursor = db.cursor()
        cursor.execute(sql)
    except (AttributeError, MySQLdb.OperationalError):
        print 'db error'
        db = MySQLdb.connect("localhost", "", "", "test")
        cursor = db.cursor()
        cursor.execute(sql)
    return cursor

def run_command(command):
    print command
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    print out
    return out

def pip_freeze():
    out = run_command("pip freeze")
    return set(out.split())

def pip_install(name, version, dep):
    package = name + "==" + version
    if dep:
        command = "pip install " + package
    else:
        command = "pip install --no-deps " + package
    run_command(command)

def pip_uninstall(name, version):
    package = name + "==" + version
    command = "pip uninstall -y " + package
    run_command(command)

def save_package_module(package_id, module_name):
    sql = """insert into crawler_module (package_id, name)
    values (""" + str(package_id) + " , '" + module_name + "')"
    query(sql)
    db.commit()

def save_module_name(module_name, name):
    pass

def iter_names(module_name):
    try:
        module = __import__(module_name)
        for name in dir(module):
            save_module_name(module_name, name)
            print "##" + name
    except:
        traceback.print_exc()


def iter_modules(path):
    return pkgutil.iter_modules([os.path.join(sys_path, path)])
#    out = run_command("vagrant ssh -c \"python -c \\\"import pkgutil; print '\\n'.join([name for _, name, _ in pkgutil.iter_modules(['" + join(sys_path, path) + "'])])\\\"\"")

def iter_modules_recur(package_id, modules, base):
    for module in modules:
        newBase = os.path.join(base, module[1])
        module_name = newBase.replace('/', '.')
        print "#" + module_name
        save_package_module(package_id, module_name)
        #iter_names(module_name)
        if module[2]:
            iter_modules_recur(package_id, pkgutil.iter_modules([os.path.join(sys_path, newBase)]), newBase)


def create_mapping(package_id, package_name, package_version):
    print 'creating mapping for ' + package_name + '==' + package_version
    pip_uninstall(package_name, package_version)
    old_modules = iter_modules('')
    old_modules_name = [name for _, name, _ in old_modules]
    print 'old modules length = ' + str(len(old_modules_name))
    print old_modules_name
    print list(old_modules)
    print old_modules
    pip_install(package_name, package_version, False)
    new_modules = iter_modules('')
#    new_modules_name = [name for _, name, _ in new_modules]
#    print 'new modules length = ' + str(len(new_modules_name))
#    print new_modules_name
    diff_modules = [x for x in new_modules if x[1] not in old_modules_name]
    diff_modules_name = [name for _, name, _ in diff_modules]
    print 'diff modules length = ' + str(len(diff_modules_name))
    print diff_modules_name
    print list(diff_modules)
    if len(diff_modules):
        print 'found modules'
        iter_modules_recur(package_id, diff_modules, '')
    else:
        print 'not found modules'
        save_package_module(package_id, 'no_modules_in_this_package')


def crawled(package_name, package_version):
    sql = """select count(*)
    from crawler_package, crawler_module
    where crawler_package.id = crawler_module.package_id
    and crawler_package.name = '""" + package_name + """'
    and crawler_package.version = '""" + package_version + "'"
    cursor = query(sql)
    result = cursor.fetchone()
    if result[0]:
        return True
    else:
        return False

def recover_packages(old_packages):
    new_packages = pip_freeze()
    diff_packages = new_packages - old_packages
    for package in diff_packages:
        print 'uninstall ' + package
        package_name, package_version = package.split("==")
        pip_uninstall(package_name, package_version)

def package_exist(package_name, package_version):
    sql = """select count(*)
    from crawler_package
    where crawler_package.name = '""" + package_name + """'
    and crawler_package.version = '""" + package_version + "'"
    cursor = query(sql)
    result = cursor.fetchone()
    if result[0]:
        return True
    else:
        return False

def get_package_id(package_name, package_version):
    sql = """select id
    from crawler_package
    where name = '""" + package_name + """'
    and version = '""" + package_version + "'"
    cursor = query(sql)
    result = cursor.fetchone()
    return result[0]

def save_package(pacakge_name, package_version):
    sql = """insert into crawler_package (package_type_id, name, version)
    values ('Django', '""" + package_name + "','" + package_version +"')"
    query(sql)
    db.commit()

if __name__ == "__main__":
    
   # sql = """select crawler_package.id, crawler_package.name, crawler_package.version
   # from crawler_package
   # """

    old_packages = pip_freeze()

    while True:
        sql = """select crawler_package.id, crawler_package.name, crawler_package.version
        from crawler_package
        where crawler_package.id not in
        (
        select crawler_package.id
        from crawler_package
        inner join crawler_module
        on crawler_package.id = crawler_module.package_id
        )
        """
        cursor = query(sql)
        results = cursor.fetchall()
        for row in results:
            try:
                recover_packages(old_packages)
                package_id = row[0]
                package_name = row[1]
                package_version = row[2]
                print """#######################################
                #######################################
                processing """ + package_name + '==' + package_version
                if crawled(package_name, package_version):
                    print 'crawled'
                    continue
                print 'old package length = ' + str(len(old_packages))
                print old_packages
                pip_install(package_name, package_version, True)
                new_packages = pip_freeze()
                print 'new package length = ' + str(len(new_packages))
                print new_packages

                diff_packages = new_packages - old_packages

                print 'diff package length = ' + str(len(diff_packages))
                print diff_packages

                if not len(diff_packages):
                    print 'install failed'
                    save_package_module(package_id, 'cant_resolve_because_install_failed')
                    continue


                for package in diff_packages:
                    package_name, package_version = package.split("==")
                    print """**********
                    **********
                    processing """ + package_name + '==' + package_version
                    if not package_exist(package_name, package_version):
                        save_package(package_name, package_version)
                        
                        
                    if not crawled(package_name, package_version):
                        package_id = get_package_id(package_name, package_version)
                        print 'package_id = ' + str(package_id)
                        create_mapping(package_id, package_name, package_version)
            except:
                traceback.print_exc()
                print "Error: unable to fecth data"

db.close()
