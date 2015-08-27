import scrapy

class DmozSpider(scrapy.Spider):
    name = "dmoz"
    allowed_domains = ["dmoz.org"]
    start_urls = [
        "http://www.dmoz.org/Computers/Programming/Languages/Python/Books/",
        "http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/"
    ]

    def parse(self, response):
        for sel in response.xpath('//ul/li'):
            title = sel.xpath('a/text()').extract()
            link = sel.xpath('a/@href').extract()
            desc = sel.xpath('text()').extract()
            print title, link, desc

    def parse_articles_follow_next_page(self, response):
	    for article in response.xpath("//article"):
	        item = ArticleItem()

	        ... extract article data here

	        yield item

	    next_page = response.css("ul.navigation > li.next-page > a::attr('href')")
	    if next_page:
	        url = response.urljoin(next_page[0].extract())
	        yield Request(url, self.parse_articles_follow_next_page)