import MySQLdb
import json
import traceback
import urllib2
import urlparse
import string
import time
token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
filename = 'repos.txt'

db = MySQLdb.connect("localhost", "", "", "test")

def query_sql(sql):
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

def query_url(url):
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            print(url)
        except:
            traceback.print_exc()
            time.sleep(5)
            continue
        return response

def user_exist(user_id):
    sql = "select count(*) from crawler_user where id = " + str(user_id)
    if query_sql(sql).fetchone()[0]:
        return True
    else:
        return False

def repo_exist(repo_id):
    sql = "select count(*) from crawler_repository where id = " + str(repo_id)
    if query_sql(sql).fetchone()[0]:
        return True
    else:
        return False

def process(reponse):
    data = json.load(response)
    user = data['owner']
    user_id = user['id']
    if not user_exist(user_id):
        user_login = user['login']
        user_url = user['url']
        sql = "insert into crawler_user (id, login, http_url) values (" + str(user_id) + ",'" + user_login + "','" + user_url + "')"
        query_sql(sql)
        db.commit()
    repo_id = data['id']
    if not repo_exist(repo_id):
        repo_name = data['name']
        repo_full_name = data['full_name']
        repo_num_tables = 0
        repo_http_url = data['html_url']
        repo_download_url = data['url'] +  "/tarball"
        repo_app_type = 'Django'
        sql = "insert into crawler_repository(id, name, full_name, owner_id, num_tables, http_url, download_url, app_type_id) values (" + str(repo_id) + ",'" + repo_name + "','" + repo_full_name + "'," + str(user_id) + "," + str(repo_num_tables) + ",'" + repo_http_url + "','" + repo_download_url + "','" + repo_app_type + "')"
        query_sql(sql)
        db.commit()

if __name__ == "__main__":
    template = string.Template("https://api.github.com/repos/${full_name}")
    with open(filename, 'r') as f:
        for line in f:
        #try:
            full_name = line.split()[0]
            sql = "insert into test_table values('" + full_name + "')"
            query_sql(sql)
            db.commit()
            #url = template.substitute(full_name=full_name)
            #response = query_url(url)
            #process(response)
            #time.sleep(10)

        #except:
        #    traceback.print_exc()
db.close()
