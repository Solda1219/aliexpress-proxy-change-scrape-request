# REFERENCE: https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/

import requests
from lxml.html import fromstring


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()

    for i in parser.xpath('//tbody/tr'):
        # print("{}:{} | {}".format(
        #     i.xpath('.//td[1]/text()'),
        #     i.xpath('.//td[2]/text()'),
        #     i.xpath('.//td[7]/text()')
        # ))
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def get_working_proxies(limit=5, proxies=None):
    test_url = "https://jsonplaceholder.typicode.com/test"
    test_response = {}
    working_proxies = []

    if not proxies:
        proxies = get_proxies()

    # TODO: repeat this until a working proxy has been found

    print("Finding {} proxies...".format(limit))
    for _proxy in proxies:
        try:
            response = requests.get(test_url, timeout=10).json()
            if response == test_response:
                working_proxies.append(_proxy)
                if limit >= 0 and len(working_proxies) >= limit:
                    break
            print("{}.....PASSED".format(_proxy))
        except Exception:
            print("{}.....FAILED".format(_proxy))
    print("Found {} working proxies : {}".format(len(working_proxies), working_proxies))
    return working_proxies
