import scrapy
from scrapy import Request
import sys
import time
from scrapy.crawler import CrawlerProcess


# custom spider class which inherits the process of the master scrapy Spider class. 
class AmazonSpider(scrapy.Spider):
    # name, permitted domains, and a hardcoded start url
    name = "Amazon"
    allowed_domains = ["amazon.com"]
    start_urls = ["https://www.amazon.com/gp/search/ref=sr_nr_p_36_0?rnid=386442011&rh=n%3A172282%2Cn%3A%21493964%2Cn%3A502394%2Cp_n_condition-type%3A2224373011%2Cp_36%3A10000-99999999%2Cn%3A281052&qid=1544518365&bbn=281052&low-price=50&high-price=",
    "https://www.amazon.com/s/ref=sr_nr_n_4?fst=as%3Aoff&rh=n%3A172282%2Cn%3A%21493964%2Cn%3A502394%2Cp_n_condition-type%3A2224373011%2Cp_36%3A10000-99999999%2Cn%3A7161070011&bbn=502394&ie=UTF8&qid=1544518525&rnid=502394",
    "https://www.amazon.com/gp/search/ref=sr_nr_n_6?fst=as%3Aoff&rh=n%3A172282%2Cn%3A%21493964%2Cn%3A502394%2Cp_n_condition-type%3A2224373011%2Cp_36%3A10000-99999999%2Cn%3A499248&bbn=502394&ie=UTF8&qid=1544518525&rnid=502394",
    "https://www.amazon.com/s/ref=sr_nr_n_8?fst=as%3Aoff&rh=n%3A172282%2Cn%3A%21493964%2Cn%3A502394%2Cp_n_condition-type%3A2224373011%2Cp_36%3A10000-99999999%2Cn%3A7161073011&bbn=502394&ie=UTF8&qid=1544518568&rnid=502394",
    "https://www.amazon.com/s/ref=sr_st?rh=n%3A172282%2Cn%3A%21493964%2Cn%3A502394%2Cp_n_condition-type%3A2224373011%2Cp_36%3A10000-99999999&qid=1544518630&bbn=502394&sort=review-rank"]

    # parsing function to seperate the response (raw page code) and return desired items
    def parse(self, response):
        def check_address(listing, s1, s2):
            a = listing.xpath(s1).extract_first().strip()
            if a[0] == '/': 
                i = listing.xpath(s2).extract_first().strip()
                return 'https://www.amazon.com/dp/' + i[i.find('_')+1:]
            else:
                return a


        category = response.xpath('.//title/text()').extract_first().strip()
        category = category[category.index('/ ')+2:]
        info_selector = '.s-item-container'
        date = time.strftime('%Y-%m-%d')

        for listings in response.css(info_selector):
            try:
                price_selector = './/span[@class="sx-price-whole"]/text()'
                name_selector = './/h2/@data-attribute'
                address_selector = './/a/@href'
                id_selector = './/a/@id'
                raw_url = listings.xpath(address_selector).extract_first()

                yield {
                    'name': listings.xpath(name_selector).extract_first().strip(),
                    'price': listings.xpath(price_selector).extract_first().strip(),
                    'address': check_address(listings, address_selector, id_selector),
                    'category_code': category,
                    'scan_date': date
                }
            except:
                yield {
                    'name': listings,
                    'price': 'null',
                    'address': 'null'
                }

            next_page_selector = './/a[@title="Next Page"]/@href'
            next_page = response.xpath(next_page_selector).extract_first()
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    callback=self.parse
                )

if __name__ == "__main__":
    # start crawler from command line arguments for testing
    process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
            'FEED_FORMAT': 'csv',
            'FEED_URI': sys.argv[1],
            'LOG_ENABLED': sys.argv[2]
        })
    process.crawl(AmazonSpider)
    process.start()

