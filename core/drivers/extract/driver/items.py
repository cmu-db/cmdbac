# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DriverItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class InputItem(scrapy.Item):
	id = scrapy.Field()
	name = scrapy.Field()
	type = scrapy.Field()
	value = scrapy.Field()

class FormItem(scrapy.Item):
	action = scrapy.Field()
	url = scrapy.Field()
	inputs = scrapy.Field()