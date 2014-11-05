from bs4 import BeautifulSoup
import urllib2
from string import Template
import time
import traceback

token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
sys_path = '/usr/local/lib/python2.7/dist-packages'
def query(url):
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            print(url)
        except:
        #except urllib2.HTTPError as e:
            traceback.print_exc()
            time.sleep(5)
            continue
        return response

def write_line(string, filename):
    with open(filename, "a") as myfile:
        myfile.write(string)
        myfile.write('\n')

if __name__ == "__main__":
    template = Template('https://github.com/search?utf8=%E2%9C%93&q=models.py+in%3Apath+filename%3Amodels.py+size%3A${size}&type=Code&ref=searchresults')
    github_host = 'https://github.com'

    for size in range(60,55000):
        url = template.substitute(size=size)
        while True:
            print url
            response = query(url)
            soup = BeautifulSoup(response.read())
            repos = soup.find_all(class_='title')
            for repo in repos:
                
                repo_name = repo.contents[1].string
                repo_time = repo.time['datetime']
                write_line(str(repo_name) + ' ' + str(repo_time), "repos.txt")
                print repo_name
                print repo_time

                

                
            
            next_page = soup.find(class_='next_page')
            if not next_page or not next_page.has_attr('href'):
                break;
            url = github_host + next_page['href']
