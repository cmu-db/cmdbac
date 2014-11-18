import urllib2
import subprocess
import traceback
import logging
import time

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

token = '5b3563b9b8c4b044530eeb363b633ac1c9535356'
def query(url):
    logging.debug('query url: ' + url)
    request = urllib2.Request(url)
    request.add_header('Authorization', 'token %s' % token)
    while True:
        try:
            response = urllib2.urlopen(request)
            header = response.info().dict;
            logging.getLogger('utils').debug('response info from: ' + url)
            logging.getLogger('utils').debug(header)

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
