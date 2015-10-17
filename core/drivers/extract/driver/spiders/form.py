# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from driver.items import InputItem, FormItem
from selenium import webdriver

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

        try:
            proxy = kwargs.get('proxy')
            service_args = [
                '--proxy=' + proxy,
                '--proxy-type=http',
            ]
        except:
            service_args = None
        self.browser = webdriver.PhantomJS(service_args=service_args)

 
    def parse_form(self, response):
        for sel in response.xpath('//form'):
            self.browser.get(response.url)
            formItem = FormItem()

            formItem['action'] = ''
            try:
                formItem['action'] = sel.xpath('@action').extract()[0]
            except:
                pass

            formItem['url'] = response.url

            formItem['method'] = ''
            try:
                formItem['method'] = sel.xpath('@method').extract()[0].lower()
            except:
                pass

            formItem['inputs'] = []
            for ip in sel.xpath('//input[@type="text" or @type="password" or @type="email"]|//textarea'):
                try:
                    id = ip.xpath('@id').extract()[0]
                except:
                    id = ''
                if id != '':
                    input_element = self.browser.find_element_by_id(id)
                    if not input_element.is_displayed():
                        continue
                name = ip.xpath('@name').extract()[0]
                try:
                    type = ip.xpath('@type').extract()[0]
                except:
                    type = ''
                inputItem = InputItem()
                inputItem['id'] = id
                inputItem['name'] = name
                inputItem['type'] = type
                inputItem['value'] = ''
                formItem['inputs'].append(inputItem)

            yield formItem
            
