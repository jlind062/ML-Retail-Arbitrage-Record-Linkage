import scrapy
import sys
import time
from scrapy.crawler import CrawlerProcess


class CraigslistSpider(scrapy.Spider):
    name = "craigslist_spider"

    def __init__(self, *a, **kw):
        super(CraigslistSpider, self).__init__(*a, **kw)
        self.start_urls = kw.get("start_urls")
        self.city = kw.get("city")
        self.time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.allowed_domains = ["craigslist.ca", "craigslist.com"]
        print(self.start_urls)

    def parse(self, response):
        item_selector = '//p[@class="result-info"]'
        for listings in response.xpath(item_selector):
            price_selector = ".//span[@class='result-price']/text()"
            name_selector = 'a ::text'
            address_selector = 'a/@href'
            url = listings.xpath(address_selector).extract_first()

            yield {
                'name': listings.css(name_selector).extract_first().strip(),
                'price': self.clean_price(listings.xpath(price_selector).extract_first()),
                'address': url,
                'city': self.city,
                'category_code': self.get_category_code(url),
                'city_code': self.get_city_code(url),
                'business': self.is_business(url),
                'scan_date': self.time
            }

            next_page_selector = './/link[@rel="next"]/@href'
            next_page = response.xpath(next_page_selector).extract_first()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse
            )

    @staticmethod
    def __after_nth_substring(string, substring, n):
        # return the string after nth occurrence of the substring
        string_trim = string
        for i in range(0, n):
            string_trim = string_trim[string_trim.find(substring) + 1:]
        return string_trim

    @staticmethod
    def clean_price(price):
        # if possible, remove the $, commas, and convert price to a float
        if price is None:
            return "Invalid"
        else:
            price = price.replace(",", "")
            return float(price[1:])

    @staticmethod
    def get_city_code(url):
        # returns the city code which is stored between the 3rd and 4th /
        url = CraigslistSpider.__after_nth_substring(url, '/', 3)
        return url[:url.index('/')]

    @staticmethod
    def is_business(url):
        # the listing is marked as a business posting if the poster identifier's
        # 3rd character is a d. Identifier is stored after the 4th /
        if CraigslistSpider.__after_nth_substring(url, '/', 4)[2] == 'd':
            return 1
        else:
            return 0

    @staticmethod
    def get_category_code(url):
        # returns the city code which is stored between the 4th and 5th /
        url = CraigslistSpider.__after_nth_substring(url, '/', 4)
        return url[:url.index('/')]


class Main:
    @staticmethod
    def run(**kwargs):
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'FEED_FORMAT': 'csv',
            'LOG_ENABLED': kwargs.get('logging'),
            'DOWNLOAD_DELAY': '2',
            'RANDOMIZE_DOWNLOAD_DELAY': '2'
        })
        Main.add_crawler(process, path=kwargs.get('path'), start_urls=[kwargs.get('start_urls')],
                         city=kwargs.get('city'))
        process.start()

    @staticmethod
    def add_crawler(crawler_process, **kwargs):
        # adds the spider to the crawler process by adding custom spider to process
        # creating custom spider class based off of original spider to override the custom_settings
        # class variable which is instantiated before the __init__ of the original spider class
        # this hacky fix is required to run multiple spiders with different feed exports
        custom_spider = type("custom_spider", (CraigslistSpider,),
                             {"custom_settings": {'FEED_URI': kwargs.get('path')}})
        crawler_process.crawl(custom_spider, start_urls=kwargs.get('start_urls'),
                              city=kwargs.get('city'))


if __name__ == "__main__":
    Main.run(path=sys.argv[1], logging=sys.argv[3],
             city=sys.argv[4], start_urls=sys.argv[2])
