import scrapy
import sys
import time
from scrapy.crawler import CrawlerProcess


class KijijiSpider(scrapy.Spider):
    name = "kijiji_spider"

    def __init__(self, *a, **kw):
        super(KijijiSpider, self).__init__(*a, **kw)
        self.start_urls = kw.get("start_urls")
        self.city = kw.get("city")
        self.time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.allowed_domains = ["kijiji.ca"]

    def parse(self, response):
        info_selector = '.info-container'
        for listings in response.css(info_selector):
            price_selector = './/div[@class="price"]/text()'
            name_selector = './/a/text()'
            address_selector = './/div[@class="title"]/a/@href'
            raw_url = 'http://www.kijiji.ca' + listings.xpath(address_selector).extract_first()

            yield {
                'name': listings.xpath(name_selector).extract_first().strip(),
                'price': self.clean_price(listings.xpath(price_selector).extract_first().strip()),
                'address': self.trim_url(raw_url),
                'city': self.city,
                'category_code': self.get_category_code(raw_url),
                'city_code': self.get_city_code(raw_url),
                'business': self.is_business(raw_url),
                'scan_date': self.time
            }

            next_page_selector = './/span[@title="Next"]/@data-href'
            next_page = 'http://www.kijiji.ca' + response.xpath(next_page_selector).extract_first()
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    callback=self.parse
                )

    @staticmethod
    def clean_price(price):
        # if possible, remove the $, commas, and convert price to a float
        price_strings = ["Please Contact", "Free", "Swap / Trade"]
        if price in price_strings:
            return "Invalid"
        else:
            price = price.replace(",", "")
            return float(price[1:])

    @staticmethod
    def __after_nth_substring(string, substring, n):
        # return the string after nth occurrence of the substring
        string_trim = string
        for i in range(0, n):
            string_trim = string_trim[string_trim.find(substring) + 1:]
        return string_trim

    @staticmethod
    def is_business(url):
        # the listing is marked as a business posting if there is a c
        # before the unique number which is after the 4th /
        if KijijiSpider.__after_nth_substring(url, '/', 6)[0] == 'c':
            return 1
        else:
            return 0

    @staticmethod
    def get_city_code(url):
        # returns the city code which is stored between the 4th and 5th /
        url = KijijiSpider.__after_nth_substring(url, '/', 4)
        return url[:url.index('/')]

    @staticmethod
    def get_category_code(url):
        # returns the city code which is stored between the 4th and 5th /
        url = KijijiSpider.__after_nth_substring(url, '/', 3)
        return url[:url.index('/')]

    @staticmethod
    def trim_url(url):
        # returns only the information required for the url to work
        if '?' in url:
            return url[:url.index('?')]
        else:
            return url


class Main:
    @staticmethod
    def run(**kwargs):
        # start the crawler with the provided logging toggle, save path, and city name
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'FEED_FORMAT': 'csv',
            'LOG_ENABLED': kwargs.get('logging')
        })
        Main.add_crawler(process, path=kwargs.get('path'), start_urls=[kwargs.get('start_urls')],
                         city=[kwargs.get('city')])
        process.start()

    @staticmethod
    def add_crawler(crawler_process, **kwargs):
        # adds the spider to the crawler process by adding custom spider to process
        # creating custom spider class based off of original spider to override the custom_settings
        # class variable which is instantiated before the __init__ of the original spider class
        # this hacky fix is required to run multiple spiders with different feed exports
        custom_spider = type("custom_spider", (KijijiSpider,),
                             {"custom_settings": {'FEED_URI': kwargs.get('path')}})
        crawler_process.crawl(custom_spider, start_urls=kwargs.get('start_urls'),
                              city=kwargs.get('city'))


if __name__ == "__main__":
    # start crawler from command line arguments for testing
    Main.run(path=sys.argv[1], logging=sys.argv[3],
             city=sys.argv[4], start_urls=sys.argv[2])
