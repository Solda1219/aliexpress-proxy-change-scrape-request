# -*- coding: utf-8 -*-
import scrapy
from math import floor
from os import getenv
import re
import os


class TPSpider(scrapy.Spider):

    name = "tp"
    # allowed_domains = ["trovaprezzi.it"]
    start_urls = ["https://www.trovaprezzi.it/"]
    custom_settings = {
        'FEED_EXPORT_FIELDS': [
            'Name',
            'ID',
            'Product URL',
            'Image URL',
            'Price',
            'Merchant',
            'Merchant Rating',
            'HTML File'
        ],
    }
    limit = int(getenv("TP_LIMIT", 999999))
    count = 0

    # Allow a custom parameter (-a flag in the scrapy command)
    def __init__(self, search="nintendo switch console"):
        self.search_string = search

    def parse(self, response):
        yield scrapy.Request(
            "https://www.trovaprezzi.it/categoria.aspx?id=168&libera={}".format(
                self.search_string.replace(' ', '+')
            ),
            callback=self.parse_link
        )

    def download_external_page(self, response, base_details={}):
        product_name = base_details['Name']
        merchant_name = base_details['Merchant']
        filepath = "trovaprezzi_htmls"
        filename = "{}/{}-{}.html".format(
            filepath,
            product_name.replace(':', "-").replace('/', '_'),
            merchant_name.replace(':', "-").replace('/', '_')
        )
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        with open(filename, "wb+") as htmlfile:
            htmlfile.write(response.body)
        base_details["HTML File"] = filename
        base_details["Product URL"] = response.url
        yield base_details

    def error_callback(self, failure, details):
        yield details

    def download_page(self, response, base_details={}):
        if 'trovaprezzi.it/goto' in response.url:
            redirect_link = response.css('a[id="click-url"]')[0].attrib['href'].split("&sid")[0]
            base_details['Product URL'] = redirect_link
            yield scrapy.Request(
                redirect_link,
                callback=self.download_external_page,
                cb_kwargs={
                    "base_details": base_details
                },
                errback=lambda f: self.error_callback(f, base_details),
            )
        else:
            yield base_details

    # Parse the search results
    def parse_link(self, response, count=0):
        # Search page is redirected to either a list of product categories
        # Or a specific category search page if the results for the search term
        # only exists in a single category

        # Sample URL if it heads straight to the results
        # https://www.trovaprezzi.it/Fprezzo_console_nintendo_switch.aspx
        # i.e. single category results
        # NOTE: URL is accessible via response.url

        filepath = "trovaprezzi_temp"
        filename = "{}/{}.html".format(filepath, response.url.replace(':', "-").replace('/', '_'))
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        with open(filename, "wb+") as htmlfile:
            htmlfile.write(response.body)

        if 'categoria' in response.url:
            relevant_products = response.css('.relevant_products > div > a')
            if len(relevant_products) > 0:
                _count = 0

                for product in relevant_products:
                    product_url = relevant_products.attrib['href']
                    product_url = "https://www.trovaprezzi.it{}".format(product_url)

                    yield scrapy.Request(
                        product_url,
                        callback=self.parse_link,
                        cb_kwargs={
                            "count": _count
                        }
                    )
                    _count = self.count
        else:
            # Extract the list of products
            results = response.css('.listing_item')
            if count + len(results) > self.limit:
                results = results[:self.limit - count]

            for product in results:
                name = product.css('.item_name::text').get().strip()
                link = product.css('.item_name').attrib['href']
                link = "https://www.trovaprezzi.it{}".format(link)

                tp_id = link.split("?")[0].split("goto/")[-1]

                image_url = product.css('.item_image > img').attrib['src']

                price = product.css('.item_basic_price::text').get().strip()
                price = price.replace('.', '').replace(',', '.').replace('€', '').strip()

                merchant = product.css('.merchant_name::text').get().strip()

                # try to get merchant rating
                merchant_rating = ""
                _merchant_rating = product.css('.merchant_reviews.rating_image')

                if _merchant_rating:
                    mr_classes = _merchant_rating[0].attrib['class'].split(' ')
                    for c in mr_classes:
                        if 'rate' in c:
                            merchant_rating = float(c.split('rate')[1])/10
                link = link.split("&sid")[0]
                base_details = {
                    "Name": name,
                    "ID": tp_id,
                    "Product URL": link,
                    "Image URL": image_url,
                    "Price": price,
                    "Merchant": merchant,
                    "Merchant Rating": merchant_rating
                }
                yield scrapy.Request(
                    link,
                    callback=self.download_page,
                    cb_kwargs={
                        "base_details": base_details,
                    },
                    errback=lambda f: self.error_callback(f, base_details),
                )
                # yield base_details

            # Get the next page
            next_page_url = response.css('a[rel="next nofollow"]')
            count += len(results)
            self.count = count

            # The last page do not have a valid url and ends with '#'
            if len(next_page_url) == 0 or count >= self.limit:
                self.log("Trovaprezzi products collected successfully !!!")
            else:
                next_url = next_page_url[0].attrib['href']
                next_url = "https://www.trovaprezzi.it{}".format(next_url)
                print('\n'+'-'*30)
                print('Next page: {}'.format(next_url))
                yield scrapy.Request(
                    next_url,
                    callback=self.parse_link,
                    cb_kwargs={
                        "count": count
                    }
                )
