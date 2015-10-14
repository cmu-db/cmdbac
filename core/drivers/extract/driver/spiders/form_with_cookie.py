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
            if formItem['action'] == '':
                try:
                    formItem['action'] = sel.xpath('@actions').extract()[0]
                except:
                    pass
            formItem['url'] = response.url
            try:
                formItem['method'] = sel.xpath('@method').extract()[0].lower()
            except:
                formItem['method'] = ''

            formItem['inputs'] = []
            for ip in sel.xpath('//input[@type="text" or @type="password" or @type="email"]|//textarea'):
                try:
                    id = ip.xpath('@id').extract()[0]
                except:
                    id = ''
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
            