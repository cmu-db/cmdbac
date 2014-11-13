import logging
from string import Template

logging.basicConfig(format='%(asctime)s %(message)s', filename='meta.log',level=logging.DEBUG)

class Meta:
    def __init__(self, name, template, min_size, threshold_size):
        self.name = name
        self.template = template
# model file less than min_size don't use database
        self.min_size = min_size
# less then 1000 files larger than threshold_size
        self.threshold_size = threshold_size
        self.cur_size = min_size

metas = []

#django_meta = Meta(name='Django', template=Template('https://github.com/search?utf8=%E2%9C%93&q=models.py+in%3Apath+filename%3Amodels.py+size%3A${size}&type=Code&ref=searchresults'), min_size=60, threshold_size=55000)
#metas.append(django_meta)

ror_meta = Meta(name='Ruby on Rails', template=Template('https://github.com/search?utf8=%E2%9C%93&q=rakefile+in%3Apath+filename%3Arakefile+size%3A${size}&type=Code&ref=searchresults'), min_size=50, threshold_size=10000)
metas.append(ror_meta)
