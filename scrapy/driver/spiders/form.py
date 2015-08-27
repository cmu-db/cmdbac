# -*- coding: utf-8 -*-

import scrapy

from driver.items import FormItem

class FormSpider(scrapy.Spider):
    name = "form"
    allowed_domains = ["dmoz.org"]
    start_urls = [
        "https://www.hackerrank.com/login",
    ]

    def parse(self, response):
        for sel in response.xpath('//form'):
            item = FormItem()
            for ip in sel.xpath('//input[@type="text" or @type="password"]'):
                name = ip.xpath('@name').extract()
                if 'inputs' in item:
                    item['inputs'].append(name)
                else:
                    item['inputs'] = [name]
            yield item
            