import amazonscraper
import aliexpress
import json
from datetime import datetime

from db import Search, create_session
from utils import store_amazon_results, store_aliexpress_results, get_product_and_pds_from_ids, update_product_details, ebay_scraper, store_ebay_results, tp_scraper, store_tp_results
from amazonscraper.client import Client
from aliexpress.client import AliexpressClient

search_param_format = {
    "amazon": {
        "keywords": {"key": "keywords", "transform": lambda x: x},
        "limit": {"key": "max_product_nb", "transform": lambda x: x},
    },
    "aliexpress": {
        "keywords": {"key": "keywords", "transform": lambda x: x},
        "limit": {"key": "max_product_nb", "transform": lambda x: x},
    },
    "ebay": {
        "keywords": {"key": "keywords", "transform": lambda x: x},
        "limit": {"key": "limit", "transform": lambda x: x},
        "filename": {"key": "filename", "transform": lambda x: x},
    },
    "tp": {
        "keywords": {"key": "keywords", "transform": lambda x: x},
        "limit": {"key": "limit", "transform": lambda x: x},
        "filename": {"key": "filename", "transform": lambda x: x},
    },
}

param_defaults = {
    "amazon": {"max_product_nb": 999999},
    "aliexpress": {"max_product_nb": 999999},
    "ebay": {"limit": 999999},
    "tp": {"limit": 999999}
}

search_functions = {
    "amazon": amazonscraper.search,
    "aliexpress": aliexpress.search,
    "ebay": ebay_scraper,
    "tp": tp_scraper,
}
store_functions = {
    "amazon": store_amazon_results,
    "aliexpress": store_aliexpress_results,
    "ebay": store_ebay_results,
    "tp": store_tp_results,
}


def scrape(site: str, search_params: dict, proxy_limit=10, client=None, return_full=False, session=None, get_pds=True) -> list:
    """
    Accepts the site to be scraped (in this case Amazon, Ebay, or Alibaba)
    Then formats the given search parameters to fit the site
    and returns the results
    @return_full: if True, returns the scraped objects with all their data, else only returns
                  id of instantiated Product objects
    """
    param_transformer = search_param_format[site]

    params = param_defaults[site]
    params = {
        param_transformer[k]["key"]: param_transformer[k]["transform"](v)
        for k, v in search_params.items()
    }

    if site == "amazon" and client is None:
        client = Client(proxy_limit=proxy_limit)
        params["client"] = client
    if site == "aliexpress" and client is None:
        client = AliexpressClient(proxy_limit=proxy_limit)
        params["client"] = client

    if not session:
        session = create_session()
    search = Search(
        search_params=json.dumps(search_params), search_date=str(datetime.now()), site=site
    )
    session.add(search)
    session.commit()

    results = search_functions[site](**params, proxy_limit=proxy_limit)
    # For amazon this returns the scraped product details
    # For ebay this returns the generated CSV
    stored_products = store_functions[site](results, search, session)
    # For amazon stored_products are the product object IDs

    if site == "amazon" and get_pds:
        print(
            "Getting product details for {} product(s)...".format(
                len(stored_products)
            )
        )

        _kwargs = get_product_and_pds_from_ids(stored_products, session)
        update_product_details(session=session, proxy_limit=proxy_limit, **_kwargs)
    if site == "aliexpress" and get_pds:
        print(
            "Getting product details for {} product(s)...".format(
                len(stored_products)
            )
        )

        _kwargs = get_product_and_pds_from_ids(stored_products, session)
        update_product_details(session=session, proxy_limit=proxy_limit, **_kwargs)

    print("="*10)
    print("Successfully scraped {} products!".format(len(stored_products)))
    print("="*10)

    return stored_products
