from constants import Constants
import urllib2

class URL:
    def __init__(self, string):
        print string
        self.string = string

    def query(self):
        request = urllib2.Request(self.string)
        request.add_header('Authorization', 'token %s' % Constants.TOKEN)
        response = urllib2.urlopen(request)
        return response
