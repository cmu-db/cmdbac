import logging
from string import Template

logging.basicConfig(format='%(asctime)s %(message)s', filename='meta.log',level=logging.DEBUG)

class Meta:
    def __init__(self, name, file_name, min_size, threshold_size):
        self.name = name
        self.template = Template("https://github.com/search?utf8=%E2%9C%93&q=" + file_name + "+in%3Apath+filename%3A" + file_name + "+size%3A${size}&type=Code&ref=searchresults")
# model file less than min_size don't use database
        self.min_size = min_size
# less then 1000 files larger than threshold_size
        self.threshold_size = threshold_size
        self.cur_size = min_size

metas = []

django_meta = Meta(name='Django', file_name='models.py', min_size=60, threshold_size=55000)
metas.append(django_meta)

#ror_meta = Meta(name='Ruby on Rails', file_name='rakefile', min_size=50, threshold_size=10000)
#metas.append(ror_meta)
