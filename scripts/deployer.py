def download(download_url, repo_id):
    request = urllib2.Request(download_url)
    request.add_header('Authorization', 'token %s' % token)
    response = urllib2.urlopen(request)
    tarName = str(repo_id) + '.tar'
    tarFile = open(tarName, 'wb')
    shutil.copyfileobj(response.fp, tarFile)
    tarFile.close()
    subprocess.call(['tar', '-xf', tarName])
    command = "tar -tf " + tarName + " | grep -o '^[^/]\+' | sort -u"
    directory = ""
    name = run_command(command)
    directory = name.rstrip('\n') + '/'
    subprocess.call(['rm', tarName])
    return directory

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


if __name__ == "__main__":
    sql = """select crawler_repository.id, crawler_repository.download_url
    from crawler_repository
    where crawler_repository.id not in
    (
    select crawler_repository.id
    from crawler_repository
    inner join crawler_attempt
    on crawler_repository.id = crawler_attempt.app_id
    )
    """
    while True:
        cursor = query_sql(sql)
        results = cursor.fetchall()
        for row in results:
            repo_id = row[0]
            download_url = row[1]
            directory_name = download(download_url, repo_id)
            setup = search_file(directory_name, 'setup.py')
            if not len(setup):
                save_attempt(repo_id, 'This is a python library', str(setup))
                delete(directory_name)
                continue

            manage = search_file(directory_name, '/manage.py')
            if not len(manage):
                save_attempt(repo_id, 'No manage.py file','')
                continue
            else if len(manage) != 1:
                save_attempt(repo_id, 'More than one manage.py file', str(manage))
                delete(directory_name)
                continue

            settings = search_file(directory_name, '/settings.py')
            if not len(settings):
                save_attempt(repo_id, 'No settings.py file','')
                delete(directory_name)
                continue
            else if len(settings) != 1:
                save_attempt(repo_id, 'More than one settings.py file', str(settings))
                delete(directory_name)
                continue

            requirements = search_file(directory_name, '/requirements.txt')

            log = runserver(directory_name, manage[0], settings[0], requirements)

            result = 'Success'

            save_attempt(repo_id, result, log)

            delete(directory_name)

            
        apps = Application.objects.filter(status=Status.objects.get(status='Found')).order_by('pk')
        for app in apps:
            #app = Application.objects.get(pk=pk)
                
            directoryName = download(app.url, app.pk)

            if app.requirements_path != '':
                installRequirements(directoryName, app.requirements_path, app.app_type)
            if app.settings_path != '':
                appendSettings(directoryName, app.settings_path)
            if app.models_path != '':
                app.model_size = count_line(directoryName, app.models_path)
            else:
                app.model_size = 0
            if app.manage_path != '':
                result = runserver(directoryName, app.pk, app.manage_path)
            else:
                result = Result.objects.get(result='Can Not Deploy')

            app.result = result
            app.status = Status.objects.get(status='Deployed')
            save(app)

            delete(directoryName)
