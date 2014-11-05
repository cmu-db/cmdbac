from bs4 import BeautifulSoup
import urllib2
from string import Template
import time
import urlparse
from pip.index import PackageFinder, Link
from pip.download import PipSession
from pip.req import InstallRequirement
import posixpath

token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
sys_path = '/usr/local/lib/python2.7/dist-packages'
host = "https://pypi.python.org/simple/"
def query(url):
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
#            print(url)
        except:
        #except urllib2.HTTPError as e:
            #traceback.print_exc()
            time.sleep(5)
            continue
        return BeautifulSoup(response.read())

def write_line(string):
    with open("links.txt", "a") as myfile:
        myfile.write(string)
        myfile.write('\n')

def get_versions(package):
    url = urlparse.urljoin(host, package)
    url = url + '/'
    session = PipSession()
    session.timeout = 15
    session.auth.prmpting = True
    pf = PackageFinder(find_links=[], index_urls="https://pypi.python.org/simple/", use_wheel=True, allow_external=[], allow_unverified=[], allow_all_external=False, allow_all_prereleases=False, process_dependency_links=False, session=session,)

    location = [Link(url, trusted=True)]
    req = InstallRequirement.from_line(package, None)
    versions = []
    for page in pf._get_pages(location, req):
        versions = versions + [version for _, _, version in pf._package_versions(page.links, package)]
    return versions

if __name__ == "__main__":
    url = "https://pypi.python.org/simple/"
    response = urllib2.urlopen(url)
    soup = BeautifulSoup(response.read())
    for link in soup.find_all("a"):
        #write_line(link.get_text())
        package = link.get('href')
        versions = get_versions(package)
        for version in versions:
            print package + "==" + version

