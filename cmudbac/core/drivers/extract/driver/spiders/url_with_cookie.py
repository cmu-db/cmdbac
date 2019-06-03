# -*- coding: utf-8 -*-

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import http.cookiejar

from driver.items import UrlItem

class UrlWithCookieSpider(CrawlSpider):
    name = "url_with_cookie"
    allowed_domains = ["127.0.0.1"]

    def __init__(self, *args, **kwargs):
        super(UrlWithCookieSpider, self).__init__(*args, **kwargs)

        self.start_urls = [kwargs.get('start_url')]
        self.cookiejar = http.cookiejar.LWPCookieJar()
        self.cookiejar.load(kwargs.get('cookie_jar'))

        self.rules = (
            Rule (SgmlLinkExtractor(allow=('')), callback='parse_url', follow=True, process_request='add_cookie_for_request'),
        )
        super(UrlWithCookieSpider, self)._compile_rules()

    def add_cookie_for_request(self, request):
        for cookie in self.cookiejar:
            request.cookies[cookie.name] = cookie.value
        logout_patterns = ['logout', 'log-out', 'log_out']
        if any(logout_pattern in request.url for logout_pattern in logout_patterns):
            return None
        return request

    def parse_url(self, response):
        urlItem = UrlItem()
        urlItem['url'] = response.url
        yield urlItem