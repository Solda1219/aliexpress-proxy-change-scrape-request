# -*- coding: utf-8 -*-
import scrapy
from os import getenv
from urllib.parse import urljoin

_BASE_URL = "https://www.amazon.it/"


class AmazonSpider(scrapy.Spider):
    name = "amazon"
    start_urls = ["https://www.amazon.it"]
    custom_settings = {
        'FEED_EXPORT_FIELDS': [
            'Name',
            'Price',
            'Link',
            'Image',
            'Rating',
            'Number of Ratings',
            'ASIN',
            'Product Overview',
            'Product Description',
            'Seller',
            'Seller Profile',
        ],
    }
    limit = int(getenv("AMAZON_LIMIT", 999999))

    # Allow a custom parameter (-a flag in the scrapy command)
    def __init__(self, search="nintendo switch console"):
        self.search_string = search

    def parse(self, response):
        # Extrach the trksid to build a search request
        # Build the url and start the requests
        yield scrapy.Request(
            "https://www.amazon.it/s?k={}".format(self.search_string.replace(' ','+')), 
            callback=self.parse_link
        )

    def parse_product_page(self, response, base_details={}):

        overview_selectors = [
            'div[id="iframeContent"]::text',  # books
            'div[id="featurebullets_feature_div"] > div > ul > li > span::text',  # bullet points
            'script[id="bookDesc_override_CSS"] + div::text',
        ]

        description_selectors = [
            'div[id="productDescription"] > p::text'
        ]

        from urllib.parse import urljoin
        _BASE_URL = "https://www.amazon.it/"

        seller_info = response.css('div[id="merchant-info"]')
        seller = ""
        seller_profile = ""
        if seller_info:
            seller_selectors = [
                'b > a',
                'a[id="sellerProfileTriggerId"]',
            ]

            for selector in seller_selectors:
                _seller = seller_info.css(selector)
                if _seller:
                    seller = _seller.css('::text').get().strip()
                    _seller_profile = _seller.attrib['href']
                    seller_profile = urljoin(_BASE_URL, _seller_profile)
                    break

            if seller == "" and seller_profile == "":
                # No seller found but may be tagged as "Ships and sold from Amazon"
                _seller = seller_info.css('::text')
                if _seller:
                    seller = _seller.get().strip()

        for selector in overview_selectors:
            overview = response.css(selector)
            if overview:
                if len(overview) > 1:
                    overview = "\n".join([
                        o.get().strip() for o in overview
                    ])
                else:
                    overview = overview.get().strip()
                break

        for selector in description_selectors:
            description = response.css(selector)
            if description:
                if len(description) > 1:
                    description = "\n".join([
                        d.get().strip() for d in description
                    ])
                else:
                    description = description.get().strip()
                break

        # if seller == "" or seller_profile == "":
        #     from scrapy.shell import inspect_response
        #     inspect_response(response, self)

        details_dict = {
            "Product Overview": overview,
            "Product Description": description,
            "Seller": seller,
            "Seller Profile": seller_profile,
        }

        base_details.update(details_dict)
        yield base_details

    # Parse the search results
    def parse_link(self, response, count=0):
        # Extract the list of products
        results = response.css('.s-result-list > .s-result-item')

        if count + len(results) > self.limit:
            results = results[:self.limit - count]

        for product in results:
            name = product.css('h2 > a > span::text').get().strip()
            link = product.css('h2 > a').attrib['href']

            link = "https://www.amazon.it{}".format(link)

            rating = product.xpath('//*[contains(text(), "su 5 stelle")]/text()').get()
            if rating:
                rating = rating.split('su')[0].strip()
            rating_count = product.css('div.a-row.a-size-small span.a-size-base::text').get()
            if rating_count:
                rating_count = rating_count.strip()

            image_url = product.css('img[data-image-latency="s-product-image"]').attrib['src']

            price = product.css('.a-price-whole::text').get()
            if price:
                price = price.replace('.', '').replace(',', '.').replace('€', '').strip()
            ASIN = None

            if 'picassoRedirect' not in link:
                ASIN = link.split("/ref=")[0].split("/")[-1]
            else:
                # Handles sponsored products
                link = urljoin(_BASE_URL, link.split("url=")[-1].replace("%2F", "/").split("/ref")[0])
                ASIN = link.split("/")[-1]

            link = link.split("/ref")[0]
            base_details = {
                "Name": name,
                "Price": price,
                "Link": link,
                "Image": image_url,
                "Rating": rating,
                "Number of Ratings": rating_count,
                "ASIN": ASIN,
            }

            yield scrapy.Request(
                link,
                callback=self.parse_product_page,
                cb_kwargs={'base_details': base_details}
            )

        # Get the next page
        _next_page_url = response.css('li.a-last > a')
        next_page_url = None
        if len(_next_page_url) > 0:
            next_page_url = _next_page_url.attrib['href']
        count += len(results)

        # The last page do not have a valid url and ends with '#'
        if not next_page_url or count >= self.limit:
            # from scrapy.shell import inspect_response
            # inspect_response(response, self)

            self.log("Amazon products collected successfully !!!")
        else:
            print('\n'+'-'*30)
            print('Next page: {}'.format(next_page_url))
            yield scrapy.Request(
                "https://www.amazon.it{}".format(next_page_url),
                callback=self.parse_link,
                cb_kwargs={
                    "count": count
                }
            )
