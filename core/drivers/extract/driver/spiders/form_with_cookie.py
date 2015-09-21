# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from driver.items import InputItem, FormItem

class FormWithCookieSpider(CrawlSpider):
    name = "form"
    allowed_domains = ["127.0.0.1"]    

    def __init__(self, *args, **kwargs): 
        super(FormSpider, self).__init__(*args, **kwargs)

        self.start_urls = [kwargs.get('start_url')]
        self.cookiejar = cookielib.LWPCookieJar()
        self.cookiejar.load(kwargs.get('cookie_jar'))
        print self.cookiejar
        
        self.rules = (
            Rule (SgmlLinkExtractor(allow=('')), callback='parse', follow=True),
        )
        super(FormSpider, self)._compile_rules()

    def parse(self, response):
        for url in self.start_urls:
            yield scrapy.Request(url, callback = self.parse_form, 
                meta = {'cookiejar': self.cookiejar})

    def parse_form(self, response):
        for sel in response.xpath('//form'):
            formItem = FormItem()

            formItem['action'] = ''
            try:
                formItem['action'] = sel.xpath('@action').extract()[0]
            except:
                pass
            if formItem['action'] == '':
                formItem['action'] = sel.xpath('@actions').extract()[0]
            formItem['url'] = response.url

            for ip in sel.xpath('//input[@type="text" or @type="password" or @type="email"]'):
                try:
                    id = ip.xpath('@id').extract()[0]
                except:
                    id = ''
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
            