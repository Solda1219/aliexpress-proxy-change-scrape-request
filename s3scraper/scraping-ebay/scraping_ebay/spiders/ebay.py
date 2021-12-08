# -*- coding: utf-8 -*-
import scrapy
from math import floor
from os import getenv
import re


class EbaySpider(scrapy.Spider):

    name = "ebay"
    allowed_domains = ["ebay.it"]
    start_urls = ["https://www.ebay.it"]
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['Name', 'Price', 'Location', 'Product Details', 'Link', 'Image', 'Seller', 'Seller Profile'],
    }
    limit = int(getenv("EBAY_LIMIT", 999999))

    # Allow a custom parameter (-a flag in the scrapy command)
    def __init__(self, search="nintendo switch console"):
        self.search_string = search

    def parse(self, response):
        # Extrach the trksid to build a search request
        trksid = response.css("input[type='hidden'][name='_trksid']").xpath("@value").extract()[0]       

        # Build the url and start the requests
        yield scrapy.Request("http://www.ebay.it/sch/i.html?_from=R40&_trksid=" + trksid +
                             "&_nkw=" + self.search_string.replace(' ','+') + "&_ipg=200", 
                             callback=self.parse_link)

    def parse_product_page(self, response, base_details={}):
        item_attr_table = response.xpath('//div[@class="itemAttr"]/div/table')

        _table = None

        try:
            _table = item_attr_table.xpath('tbody')
            if len(_table == 0):
                _table = item_attr_table
        except Exception:
            _table = item_attr_table

        details = {}

        for row in _table.xpath('tr'):
            columns = row.xpath('td')
            for _i in range(floor(len(columns) / 2)):
                i = _i * 2
                key = columns[i].xpath('text()').get().strip().strip(":")
                value = ""
                try:
                    value = columns[i + 1].xpath('div/span/text()').extract_first().strip()
                except Exception:
                    value = columns[i + 1].xpath('span/text()').extract_first().strip()
                details[key] = value

        _details = "".join(["{}: {}\n".format(k, v) for k, v in details.items()])

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        _seller = response.xpath('//span[@class="mbg-nw"]')[0]
        seller = _seller.xpath('text()').extract_first().strip()
        seller_url = _seller.xpath('..').attrib['href']

        details_dict = {
            "Product Details": _details,
            "Seller": seller,
            "Seller Profile": seller_url,
        }

        base_details.update(details_dict)
        return base_details

    # Parse the search results
    def parse_link(self, response, count=0):
        # Extract the list of products
        results = response.xpath('//li[@class="sresult lvresult clearfix li"]')

        if count + len(results) > self.limit:
            results = results[:self.limit - count]

        for product in results:
            _name = [
                n.get().strip() for n in product.xpath('.//*[@class="lvtitle"]//text()')
                if n.get().strip() != ''
            ]
            name = _name[-1]
            # Sponsored or New Listing links have a different class
            if not name:
                name = product.xpath('.//*[@class="lvtitle lvtitle--has-tags"]/text()').extract_first()
                if not name:
                    name = product.xpath('.//*[@class="lvtitle lvtitle--has-tags"]//text()').extract_first()
            if name == 'New Listing':
                name = product.xpath('.//*[@class="lvtitle"]//text()').extract()[1]

            # If this get a None result
            if not name:
                name = "ERROR"

            link = product.xpath('.//*[@class="lvtitle"]/a').attrib['href']
            image_url = product.xpath('.//img').attrib['src']

            _price = product.xpath('.//*[@class="lvprice prc"]//text()')
            prices = []
            for p in _price:
                if not re.match(r".*[a-zA-Z]+.*", p.get()) and p.get().strip() != '':
                    prices.append(p.get().strip())

            price = " / ".join(prices)
            price = price.replace('.', '').replace(',', '.')
            location = ""
            try:
                location = product.xpath('.//ul[@class="lvdetails left space-zero full-width"]/li/text()')[0].get().strip()
            except Exception:
                pass

            base_details = {
                "Name": name,
                "Price": price,
                "Location": location,
                "Link": link,
                "Image": image_url,
            }

            yield scrapy.Request(
                link,
                callback=self.parse_product_page,
                cb_kwargs={'base_details': base_details}
            )

        # Get the next page
        next_page_url = response.xpath('//*/a[@class="gspr next"][0]/@href').extract_first()
        count += len(results)

        # The last page do not have a valid url and ends with '#'
        if not next_page_url or str(next_page_url).endswith("#") or count >= self.limit:
            self.log("eBay products collected successfully !!!")
        else:
            print('\n'+'-'*30)
            print('Next page: {}'.format(next_page_url))
            yield scrapy.Request(
                next_page_url,
                callback=self.parse_link,
                cb_kwargs={
                    "count": count
                }
            )
