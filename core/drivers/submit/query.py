import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import mechanize

def query_url(url, br = None):
    if br == None:
        br = mechanize.Browser()
        br.set_handle_robots(False)
    
    br.open(url['url'].encode("ascii","ignore"))

    return
