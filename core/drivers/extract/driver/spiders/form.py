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

    def closed(self, reason):
        self.browser.quit()
 
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
            for ip in sel.xpath('.//input|.//textarea'):
                try:
                    _id = ip.xpath('@id').extract()[0]
                except:
                    _id = ''
                if _id != '':
                    input_element = self.browser.find_element_by_id(_id)
                    if not input_element.is_displayed():
                        continue
                name = ip.xpath('@name').extract()[0]
                try:
                    _type = ip.xpath('@type').extract()[0]
                except:
                    _type = 'textarea'
                try:
                    value = ip.xpath('@value').extract()[0]
                except:
                    value = ''
                inputItem = InputItem()
                inputItem['id'] = _id
                inputItem['name'] = name
                inputItem['type'] = _type
                inputItem['value'] = value
                formItem['inputs'].append(inputItem)

            try:
                _id = sel.xpath('@id').extract()[0]
            except:
                _id = ''
            try:
                _class = sel.xpath('@class').extract()[0]
            except:
                _class = ''
            try:
                enctype = sel.xpath('@enctype').extract()[0]
            except:
                enctype = ''
            formItem['id'] = _id
            formItem['clazz'] = _class
            formItem['enctype'] = enctype

            yield formItem
            
