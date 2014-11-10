import urllib2
import subprocess

token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
def query(url):
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            print('response from: ' + url)
        except urllib2.HTTPError as e:
            traceback.print_exc()
            time.sleep(5)
            continue
        return response

def run_command(command):
    print 'run command: ' + command
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    print 'output: ' + out
    return out
