# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from driver.items import InputItem, FormItem

class FormSpider(CrawlSpider):
    name = "form"
    # allowed_domains = ["www.hackerrank.com"]
    # start_urls = ["https://www.hackerrank.com/login"]

    rules = (Rule (LinkExtractor(), callback="parse_form", follow= True),
    )

    def parse(self, response):
        for sel in response.xpath('//form'):
            formItem = FormItem()
            for ip in sel.xpath('//input[@type="text" or @type="password"]'):
                id = ip.xpath('@id').extract()
                name = ip.xpath('@name').extract()
                type = ip.xpath('@type').extract()
                inputItem = InputItem()
                inputItem['id'] = id
                inputItem['name'] = name
                inputItem['type'] = type
                if 'inputs' in formItem:
                    formItem['inputs'].append(inputItem)
                else:
                    formItem['inputs'] = [inputItem]
            yield formItem
            