# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import cookielib

from driver.items import InputItem, FormItem

class FormWithCookieSpider(CrawlSpider):
    name = "form_with_cookie"
    allowed_domains = ["127.0.0.1"]    

    def __init__(self, *args, **kwargs): 
        super(FormWithCookieSpider, self).__init__(*args, **kwargs)

        self.start_urls = [kwargs.get('start_url')]
        self.cookiejar = cookielib.LWPCookieJar()
        self.cookiejar.load(kwargs.get('cookie_jar'))
        
        self.rules = (
            Rule (SgmlLinkExtractor(allow=('')), callback='parse_form', follow=True, process_request='add_cookie_for_request'),
        )
        super(FormWithCookieSpider, self)._compile_rules()

    def add_cookie_for_request(self, request):
        for cookie in self.cookiejar:
            request.cookies[cookie.name] = cookie.value
        logout_patterns = ['logout', 'log-out', 'log_out']
        if any(logout_pattern in request.url for logout_pattern in logout_patterns):
            return None
        return request
   
    def parse_form(self, response):
        for sel in response.xpath('//form'):
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
            for ip in sel.xpath('.//input[not(@type="hidden") and not(@type="submit")]|.//textarea'):
                try:
                    _id = ip.xpath('@id').extract()[0]
                except:
                    _id = ''
                name = ip.xpath('@name').extract()[0]
                try:
                    _type = ip.xpath('@type').extract()[0]
                except:
                    _type = 'textarea'
                inputItem = InputItem()
                inputItem['id'] = _id
                inputItem['name'] = name
                inputItem['type'] = _type
                inputItem['value'] = ''
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
            
