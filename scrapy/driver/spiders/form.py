# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from driver.items import FormItem

class FormSpider(CrawlSpider):
    name = "form"
    allowed_domains = ["www.hackerrank.com"]
    start_urls = [
        "https://www.hackerrank.com/login",
    ]

    rules = (Rule (LinkExtractor(), callback="parse_form", follow= True),
    )

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
            