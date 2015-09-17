# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from driver.items import InputItem, FormItem

class FormSpider(CrawlSpider):
    name = "form"
    allowed_domains = ["127.0.0.1"]    

    def __init__(self, *args, **kwargs): 
        super(FormSpider, self).__init__(*args, **kwargs)

        self.start_urls = [kwargs.get('start_url')]
        
        follow = True if kwargs.get('follow') == 'true' else False
        self.rules = (
            Rule (SgmlLinkExtractor(allow=('')), callback='parse_form', follow=follow),
        )
        super(FormSpider, self)._compile_rules()

 
    def parse_form(self, response):
        for sel in response.xpath('//form'):
            formItem = FormItem()
            formItem['action'] = sel.xpath('@action').extract()[0]
            formItem['url'] = response.url
            for ip in sel.xpath('//input[@type="text" or @type="password" or @type="email"]'):
                id = ip.xpath('@id').extract()[0]
                name = ip.xpath('@name').extract()[0]
                type = ip.xpath('@type').extract()[0]
                inputItem = InputItem()
                inputItem['id'] = id
                inputItem['name'] = name
                inputItem['type'] = type
                if 'inputs' in formItem:
                    formItem['inputs'].append(inputItem)
                else:
                    formItem['inputs'] = [inputItem]
            yield formItem
            