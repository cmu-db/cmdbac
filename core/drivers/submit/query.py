import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

def query_url(url, br = None):
    if br == None:
        br = mechanize.Browser()
    
    br.open(url['url'].encode("ascii","ignore"))

    return
