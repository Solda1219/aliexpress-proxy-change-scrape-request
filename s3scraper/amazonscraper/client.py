# -*- coding: utf-8 -*-
"""
Module to get and parse the product info on Amazon
"""

import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from amazonscraper.proxy_scrape import get_proxies
from itertools import cycle
import time
from amazonscraper.logger import AmazonLogPrinter as _print

_BASE_URL = "https://www.amazon.it/"
_DEFAULT_BEAUTIFULSOUP_PARSER = "html.parser"
_DEFAULT_USER_AGENT = 'Mozilla/5.0 (Linux; Android 7.0; \
SM-A520F Build/NRD90M; wv) AppleWebKit/537.36 \
(KHTML, like Gecko) Version/4.0 \
Chrome/65.0.3325.109 Mobile Safari/537.36'
_CHROME_DESKTOP_USER_AGENT = 'Mozilla/5.0 (Macintosh; \
Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/67.0.3396.79 Safari/537.36'

_USER_AGENT_LIST = [
    _DEFAULT_USER_AGENT,
    _CHROME_DESKTOP_USER_AGENT,
]

_CSS_SELECTORS_MOBILE = {
    "product": "#resultItems > li",
    "title": "a > div > div.sx-table-detail > h5 > span",
    "rating": "a > div > div.sx-table-detail > \
               div.a-icon-row.a-size-small > i > span",
    "review_nb": "a > div > div.sx-table-detail > \
                  div.a-icon-row.a-size-small > span",
    "url": "a[href]",
    "img": "img[src]",
    "next_page_url": "ul.a-pagination > li.a-last > a[href]",
}
# Sometimes, the result page is displayed with another layout
_CSS_SELECTORS_MOBILE_GRID = {
    "product": "#grid-atf-content > li > div.s-item-container",
    "title": "a > div > h5.sx-title > span",
    "rating": "a > div > div.a-icon-row.a-size-mini > i > span",
    "review_nb": "a > div > div.a-icon-row.a-size-mini > span",
    "url": "a[href]",
    "img": "img[src]",
    "next_page_url": "ul.a-pagination > li.a-last > a[href]",
}
_CSS_SELECTORS_DESKTOP = {
    "product": "ul > li.s-result-item > div.s-item-container",
    "title": "a.s-access-detail-page > h2",
    "rating": "i.a-icon-star > span",
    "review_nb": "div.a-column.a-span5.a-span-last > \
                div.a-row.a-spacing-mini > \
                a.a-size-small.a-link-normal.a-text-normal",
    "url": "div.a-row.a-spacing-small > div.a-row.a-spacing-none > a[href]",
    "img": "div.a-column.a-span12.a-text-center > a.a-link-normal.a-text-normal > img[src]",
    "next_page_url": "a#pagnNextLink",
}
_CSS_SELECTORS_DESKTOP_2 = {
    "product": "div.s-result-list.sg-row > div.s-result-item",
    "title": "div div.sg-row  h5 > span",
    "rating": "div div.sg-row .a-spacing-top-mini i span",
    "review_nb": "div div.sg-row .a-spacing-top-mini span.a-size-small",
    "url": "div div a.a-link-normal",
    "img": "img[src]",
    "next_page_url": "li.a-last > a[href]",
}

_CSS_SELECTOR_LIST = [
                        _CSS_SELECTORS_MOBILE,
                        _CSS_SELECTORS_MOBILE_GRID,
                        _CSS_SELECTORS_DESKTOP,
                        _CSS_SELECTORS_DESKTOP_2,
                     ]

# Maximum number of requests to do if Amazon returns a bad page (anti-scraping)
_MAX_TRIAL_REQUESTS = 5
_WAIT_TIME_BETWEEN_REQUESTS = 1


class Client(object):
    """Do the requests with the Amazon servers"""

    def __init__(self, proxy_limit=10):
        """ Init of the client """
        self.session = requests.session()
        self.current_proxy = ""

        self._proxies = list(get_proxies())
        self._proxies = self._get_working_proxies(limit=proxy_limit)
        self.proxies = cycle(self._proxies)
        # _print("PROXIES: {}".format(self._proxies))
        self._change_session_proxy()

        self.current_user_agent_index = 0
        self.headers = {
                    'Host': 'www.amazon.it',
                    'User-Agent': _USER_AGENT_LIST[0],
                    'Accept': 'text/html,application/xhtml+xml,\
                        application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    }
        self.product_dict_list = []
        self.html_pages = []

    def _change_user_agent(self):
        """ Change the User agent of the requests
        (useful if anti-scraping)
        >>> c = Client()
        >>> c.current_user_agent_index
        0
        >>> c.headers['User-Agent'] == _USER_AGENT_LIST[0]
        True
        >>> c._change_user_agent()
        >>> c.current_user_agent_index
        1
        >>> c.headers['User-Agent'] == _USER_AGENT_LIST[1]
        True
        >>> c2 = Client()
        >>> for i in range(0,9): c2._change_user_agent()
        >>> c2.current_user_agent_index == 9 % len(_USER_AGENT_LIST)
        True
        """
        index = (self.current_user_agent_index + 1) % len(_USER_AGENT_LIST)
        self.headers['User-Agent'] = _USER_AGENT_LIST[index]
        self.current_user_agent_index = index
    
    def _get_working_proxies(self, limit=-1):
        test_url = "https://jsonplaceholder.typicode.com/test"
        test_response = {}
        working_proxies = []

        self.proxy_limit = limit

        # TODO: repeat this until a working proxy has been found

        _print("Finding {} proxies...".format(limit))
        for _proxy in self._proxies:
            self.session.proxies.update({'http': _proxy, 'https': _proxy})
            try:
                response = self.session.get(test_url, timeout=10).json()
                if response == test_response:
                    working_proxies.append(_proxy)
                    if limit >= 0 and len(working_proxies) >= limit:
                        break
                _print("{}.....PASSED".format(_proxy))
            except Exception:
                _print("{}.....FAILED".format(_proxy))
        _print("Found {} working proxies : {}".format(len(working_proxies), working_proxies))


        if len(working_proxies) == 0:
            raise Exception("ERROR: No working proxies found!")
        return working_proxies

    def _change_session_proxy(self):
        _proxy = next(self.proxies)
        self.current_proxy = _proxy
        self.session.proxies.update({'http': _proxy, 'https': _proxy})

        # TODO: test if proxy is working, if not remove from cycle
        # check if cycle is non-empty, if empty get new proxies
        # this should make it more resilient for when proxies start failing
        # and new ones have to be used
    
    def _remove_current_proxy(self):
        cur_prox_index = self._proxies.index(self.current_proxy)
        _print("Removing current proxy")
        if len(self._proxies) > 1:
            if cur_prox_index == len(self._proxies) - 1:
                self._proxies = self._proxies[:-1]
                self.proxies = cycle(self._proxies)
            else:
                self._proxies = self._proxies[cur_prox_index+1:] + self._proxies[:cur_prox_index]
                self.proxies = cycle(self._proxies)
        else:
            _print("Proxy pool depleted, replenishing...")
            self.proxies = cycle(self._get_working_proxies(limit=self.proxy_limit))
        # _print("Current proxies: {}".format(self._proxies))
        time.sleep(5)

    def _get(self, url, retries=0, retry_limit=5, rotate_proxies=False):
        """ GET request with the proper headers """
        try:
            if rotate_proxies:
                self._change_session_proxy()
            _print("Attempting to get {}".format(url))
            ret = self.session.get(url, headers=self.headers, timeout=10)
            if ret.status_code != 200:
                retries = retry_limit
                raise ConnectionError(
                    'Status code {status} for url {url}'.format(
                        status=ret.status_code, url=url))
            return ret
        except Exception as e:
            _print("Proxy error, changing proxies and retrying [Attempt: {}/{}] | {}".format(retries, retry_limit, e))
            self._remove_current_proxy()
            self._change_session_proxy()
        if retries < retry_limit:
            return self._get(url, retries+1, retry_limit)
        else:
            raise Exception("Failed to fetch {} within the given retry limit({})!".format(url, retry_limit))


    def _update_headers(self, search_url):
        """ Update the 'Host' field in the header with the proper Amazon domain
        >>> c = Client()
        >>> _print(c.headers['Host'])
        www.amazon.com
        >>> c._update_headers("https://www.amazon.fr/s/lkdjsdlkjlk")
        >>> _print(c.headers['Host'])
        www.amazon.fr
        """
        self.base_url = "https://" + \
            search_url.split("://")[1].split("/")[0] + "/"
        self.headers['Host'] = self.base_url.split("://")[1].split("/")[0]

    def _get_search_url(self, keywords):
        """ Get the Amazon search URL, based on the keywords passed
        >>> c = Client()
        >>> _print(c._get_search_url(keywords="python"))
        https://www.amazon.com/s?k=python
        """
        search_url = urljoin(_BASE_URL, ("s?k=%s" % (keywords)))
        return search_url

    def _check_page(self, html_content):
        """Check if the page is a valid result page
        (even if there is no result) """
        if "Sign in for the best experience" in html_content:
            valid_page = False
            error = "sign_in"
        elif "The request could not be satisfied." in html_content:
            valid_page = False
            error = "request_error"
        elif "Robot Check" in html_content:
            valid_page = False
            error = "automation_block"
        elif "api-services-support@amazon.com" in html_content:
            valid_page = False
            error = "automation_block"
        else:
            return {'valid_page': True}
            valid_page = True
        return {'valid_page': valid_page, "error": error}


    def _get_page_html(self, search_url):
        """Retrieve the page at `search_url`"""
        trials = 0
        res = None

        valid_page = False

        while trials < _MAX_TRIAL_REQUESTS:

            _print('Trying user agent: {}'.format(self.headers['User-Agent']))
            trials += 1
            try:
                res = self._get(search_url)

                validation_results = self._check_page(res.text)
                valid_page = validation_results['valid_page']
                if not valid_page:
                    _print("WARNING: Found a non-valid page! (probably robot check)")
                    if validation_results['error'] in ["automation_block"]:
                        self._remove_current_proxy()

            # To counter the "SSLError bad handshake" exception
            except requests.exceptions.SSLError:
                valid_page = False

            except ConnectionError:
                valid_page = False

            if valid_page:
                break

            self._change_user_agent()
            self._change_session_proxy()
            time.sleep(_WAIT_TIME_BETWEEN_REQUESTS)

        if not valid_page:
            raise ValueError('No valid pages found! Perhaps the page returned is a CAPTCHA? Check products.last_html_page')
        return res.text

    def _get_n_ratings(self, product):
        """Given the HTML of a `product`, extract the number of ratings"""

        n_ratings_css_selectors = [
            "span[id='acrCustomerReviewText']",
            "div.a-row.a-size-small span.a-size-base",
            "div div.sg-row .a-spacing-top-mini span.a-size-small",
            "div.a-column.a-span5.a-span-last > div.a-row.a-spacing-mini > a.a-size-small.a-link-normal.a-text-normal",
        ]

        for selector in n_ratings_css_selectors:

            n_ratings = _css_select(product, selector)

            try:
                # rating text is "n voti" so split by whitespace
                # to get the number then remove comma to turn into int
                n_ratings = int(n_ratings.split(" ")[0].replace(',', ''))
                break
            except ValueError:
                pass

        if not n_ratings:
            # _print('  Failed to extract number of ratings!')
            return float('nan')

        return n_ratings


    def _get_title(self, product):
        """Given the HTML of a `product`, extract the title"""

        title_css_selectors = [
            'h2 span',
            'h5 span',
            "a.s-access-detail-page > h2",
            "div div.sg-row  h5 > span",
            "span[id='productTitle']",
        ]

        for selector in title_css_selectors:

            title = _css_select(product, selector)

            if title:
                break

        if not title:
            # _print('  Failed to extract title!')
            pass

        return title


    def _get_rating(self, product):
        """Given the HTML of a `product`, extract the average rating"""

        # rating_string_en = " out of 5"
        rating_string_it = " su 5 stelle"

        rating = re.search(r'(\d.\d){}'.format(rating_string_it), str(product))

        if rating:
            rating = rating.groups()[0]
            # convert string to float and replace European decimal seperator ',' with '.'s
            rating = float(rating.replace(",", "."))
        else:
            rating = float('nan')
            # _print('  Failed to extract rating!')

        return rating


    def _get_prices(self, product):
        """
        Given the HTML of a `product`, extract all prices.
        """
        # XXX currently does not handle shipping prices or prices for the
        # various formats of books.

        # match all prices of the form $X,XXX.XX:
        price_regex = r'[\d\.]+\,\d\d\s*\???'
        raw_prices = product.find_all(text=re.compile(price_regex))


        prices = {
            'prices_per_unit': set(),
            'units': set(),
            'prices_main': set(),
        }

        # attempt to identify the prices
        original_prices = []
        for raw_price in raw_prices:

            # get the price as a float rather than a string or BeautifulSoup object
            cleaned_up_price = raw_price.replace('.', '').replace(',', '.').replace('???', '').strip()

            price = 0.0

            try:
                price = float(re.match(r'([0-9]+\.*[0-9]*).*', cleaned_up_price).groups()[0])
            except Exception:
                # _print("CLEANED UP PRICE:{}".format(cleaned_up_price))
                pass
                # raise Exception("PRICE PARSING ERROR")

            # ignore promotional strikethrough prices
            if raw_price.parent.parent.attrs.get('data-a-strike') == 'true' or price in original_prices:
                if price not in original_prices:
                    original_prices.append(price)
                continue

            # ignore promotional freebies
            elif raw_price == '0,00???':
                continue

            # extract price per unit price and unit
            elif raw_price.startswith('(') and '/' in raw_price:
                price_per_unit = re.findall(r'/(.*)\)', raw_price)[0]
                prices['prices_per_unit'].add(price)
                prices['units'].add(price_per_unit)

            # any other price is hopefully the main price
            else:
                prices['prices_main'].add(price)

        # clean up the discoverd prices
        for price_type, price_value in prices.copy().items():

            if len(price_value) == 0:
                prices[price_type] = float('nan')

            elif len(price_value) == 1:
                prices[price_type] = price_value.pop()

            else:
                _print('  Multiple prices found. Consider selecting a format on Amazon and using that URL!')
                # if len(original_prices) > 0:
                #     _print('  Using found original (strikethroughed) price! {}'.format(original_prices))
                #     prices[price_type] = str(original_prices[0])
                # else:
                prices[price_type] = ', '.join(map(str, price_value))
                # import ipdb
                # ipdb.set_trace()

        return prices

    def _extract_page(self, page, max_product_nb):
        """
        Extract the products on a given HTML page of Amazon results and return
        the URL of the next page of results
        """

        soup = BeautifulSoup(page, _DEFAULT_BEAUTIFULSOUP_PARSER)

        # shuffle through CSS selectors until we get a list of products
        selector = 0
        for css_selector_dict in _CSS_SELECTOR_LIST:
            selector += 1
            css_selector = css_selector_dict.get("product", "")
            products = soup.select(css_selector)

            if len(products) >= 1:
                break

        # For each product of the result page
        for product in products:

            # Check if the maximum number to search has been reached
            if len(self.product_dict_list) >= max_product_nb:
                break

            product_dict = {}

            # extract title
            product_dict['title'] = self._get_title(product)

            # _print('Extracting {}'.format(product_dict['title'][:80]))

            # extract rating
            product_dict['rating'] = self._get_rating(product)

            # extract number of ratings
            product_dict['review_nb'] = self._get_n_ratings(product)

            # Get image before url and asin
            css_selector = css_selector_dict.get("img", "")
            img_product_soup = product.select(css_selector)
            if img_product_soup:
                img_url = img_product_soup[0].get('src')
                # Check if it is not a base64 formatted image
                if "data:image/webp" in img_url:
                    img_url = img_product_soup[0].get(
                        'data-search-image-source-set',
                        '').split(' ')[0]

                if img_url != '':
                    img_url = _get_high_res_img_url(img_url=img_url)

                product_dict['img'] = img_url

            # Extract ASIN and product URL
            css_selector = css_selector_dict.get("url", "")

            url_product_soup = product.select(css_selector)

            product_dict['url'] = ''
            product_dict['asin'] = ''

            if url_product_soup:
                url = urljoin(
                    self.base_url,
                    url_product_soup[0].get('href'))

                if 'picassoRedirect' not in url:
                    product_dict['url'] = url.split("/ref=")[0]
                    product_dict['asin'] = product_dict['url'].split("/")[-1]
                else:
                    # Handles sponsored products
                    product_dict['url'] = urljoin(_BASE_URL, url.split("url=")[-1].replace("%2F", "/").split("/ref")[0])
                    product_dict['asin'] = product_dict['url'].split("/")[-1]
            if not product_dict['url']:

                _print('  Failed to extract URL!')
                pass

            if not product_dict['asin']:

                _print('  Failed to extract ASIN!')
                pass


            # Amazon has many prices associated with a given product
            prices = self._get_prices(product)
            product_dict.update(prices)

            self.product_dict_list.append(product_dict)


        css_selector = css_selector_dict.get("next_page_url")
        url_next_page_soup = soup.select(css_selector)
        if url_next_page_soup:
            url_next_page = urljoin(
                self.base_url,
                url_next_page_soup[0].get('href'))
        else:
            raise(ValueError('Could not find the URL of the next page of results!'))
        return url_next_page


    def _get_products(self, keywords="", search_url="", max_product_nb=100):

        if search_url == "":
            search_url = self._get_search_url(keywords)
        self._update_headers(search_url)

        product_count = 0

        page_number = 1

        if max_product_nb < 0:
            max_product_nb = 999999

        while len(self.product_dict_list) < max_product_nb:

            # TODO: make this part interruptible
            # also, temporarily store pages in files so that we can process this by chunks

            # get the html of the specified page
            page = self._get_page_html(search_url)
            self.html_pages.append(page)

            # extract the needed products from the page and return the url of
            # the next page

            # if "page=" in search_url:
            #     page_number = int(re.match(r'.*page=([0-9]+)', search_url).groups()[0])
            _print("Scraping page {}".format(page_number))

            _print("Attempting to get URL for page {} |".format(page_number + 1))
            try:
                search_url = self._extract_page(page, max_product_nb=max_product_nb)
            except ValueError as e:
                # _print("Failed to get next url | {}".format(e))
                if "page=" in search_url:
                    search_url =  re.sub(r'(.*page=)([0-9]+)(.*)', r"\g<1>{}\g<3>".format(page_number+1), search_url)
                else:
                    search_url += "&page={}".format(page_number + 1)
                # _print("Attempting to build URL manually: {}".format(search_url))
            _print("Products found on page {}: {}".format(page_number, len(self.product_dict_list) - product_count))
            page_number += 1
            if len(self.product_dict_list) == product_count:
                _print("No more results found")
                break
            product_count = len(self.product_dict_list)

        _print("Found {} products".format(len(self.product_dict_list)))
        return self.product_dict_list

    def _get_product_page(self, url: str, rotate_proxies=True, max_retries=5):
        retries = 0
        while retries < max_retries:
            try:
                page = self._get(url, rotate_proxies=rotate_proxies)
                if "api-services-support@amazon.com" in page.text:
                    self._remove_current_proxy()
                    continue
                else:
                    return page
            except Exception as e:
                _print("WARNING: error while getting {}, retrying... | {}".format(url, e))
                pass
            retries += 1
        raise Exception("ERROR: Page cannot be accessed for {}".format(url))

    def _get_product_details(self, products: list) -> dict:
        '''
        products should be an array of product dicts with at least ASIN and url
        returns an array with dict containing ASIN + scraped product detail
        '''

        # _print("PRODUCTS: {}".format(products))

        details_pair = {}
        for product in [p for p in products if p['url'].strip() != ""]:
            try:
                page = self._get_product_page(product['url'], rotate_proxies=True)
            except Exception as e:
                _print("Cannot access {} for {} | {}".format(product['url'], product['name'], e))
                details_pair[product['ASIN']] = {}
                continue
            soup = BeautifulSoup(page.text, _DEFAULT_BEAUTIFULSOUP_PARSER)

            css_selectors = ["div[id='productDescription_fullView']", 'div[id="iframeContent"]']
            details = None
            for selector in css_selectors:
                selection = soup.select(selector)
                if len(selection) > 0:
                    details = selection[0].text.strip()
                    break
            if not len(selection) > 0:
                # try regexing the description
                try:
                    _desc = re.search(
                        r'id="productDescription_fullView"\>(.*)?\<\/p><\/div>',
                        "".join(str(soup.contents)).replace("\n", "")
                    ).groups()[0]
                    details = _desc.split("<p>")[-1]
                    details = details.split("</div>")[0]
                    details = details.replace("<br>", "\n")
                    details = re.sub(r'\<.*?\>', '', details)
                except Exception:
                    _print("No description found for {} | Possibly no description was provided in page!".format(product['url']))
                    pass
            if details:
                # details = selection[0].text.strip()
                details_pair[product['ASIN']] = {"description": details}
                _print("FOUND DESCRIPTION FOR {}:\n {}".format(product['url'], details))

            else:
                details_pair[product['ASIN']] = {}
                # raise Exception("ERROR: no product description found for {}".format(product.url))
        return details_pair


def _css_select(soup, css_selector):
    """
    Returns the content of the element pointed by the CSS selector, or an empty
    string if not found
    """
    selection = soup.select(css_selector)
    retour = ""
    if len(selection) > 0:
        if hasattr(selection[0], 'text'):
            retour = selection[0].text.strip()
    return retour

def _get_high_res_img_url(img_url):
    """ Returns a modified url pointing to the high resolution version of
    the image
    >>> _print(_get_high_res_img_url("https://images-na.ssl-images-amazon.com/\
images/I/513gErH1dML._AC_SX236_SY340_FMwebp_QL65_.jpg"))
    https://images-na.ssl-images-amazon.com/\
images/I/513gErH1dML.jpg
    >>> _print(_get_high_res_img_url("https://images-na.ssl-images-amazon.com/\
images/I/51F48HFHq6L._AC_SX118_SY170_QL70_.jpg"))
    https://images-na.ssl-images-amazon.com/\
images/I/51F48HFHq6L.jpg
    """
    high_res_url = img_url.split("._")[0] + ".jpg"
    return high_res_url
