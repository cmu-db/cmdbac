import urllib2
import subprocess
import traceback
import logging
logging.basicConfig(format='%(asctime)s %(message)s', filename='utils.log', level=logging.DEBUG)

token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
def query(url):
    logging.debug('query url: ' + url)
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            header = response.info().dict;
            logging.debug('response info from: ' + url)
            logging.debug(header)

        except:
            logging.debug(traceback.print_exc())
            time.sleep(5)
            continue
        return response

def run_command(command):
    logging.debug('run command: ' + command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    logging.debug('output: ' + out)
    logging.debug('stderr: ' +err)
    return out
