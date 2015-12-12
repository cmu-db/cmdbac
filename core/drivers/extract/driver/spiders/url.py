# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from driver.items import UrlItem

class UrlSpider(CrawlSpider):
    name = "url"
    allowed_domains = ["127.0.0.1"]    

    def __init__(self, *args, **kwargs): 
        super(UrlSpider, self).__init__(*args, **kwargs)

        self.start_urls = [kwargs.get('start_url')]
        
        follow = True if kwargs.get('follow') == 'true' else False
        self.rules = (
            Rule (SgmlLinkExtractor(allow=('')), callback='parse_url', follow=follow),
        )
        super(UrlSpider, self)._compile_rules()

        try:
            proxy = kwargs.get('proxy')
            service_args = [
                '--proxy=' + proxy,
                '--proxy-type=http',
            ]
        except:
            service_args = None
        
    def parse_url(self, response):
        urlItem = UrlItem()
        urlItem['url'] = response.url
        yield urlItem
