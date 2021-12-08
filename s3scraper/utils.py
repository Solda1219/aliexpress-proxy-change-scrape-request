import csv
import subprocess
from math import ceil
import os

from amazonscraper.client import Client
from aliexpress.client import AliexpressClient
from db import AmazonProduct, AliexpressProduct, EbayProduct, ProductDetail, create_session


def amazon_transformer(product: dict) -> dict:
    arg_transform = {
        "prices_per_unit": "price_per_unit",
        "units": "units",
        "description": "description",
    }
    optional_args = {
        arg_transform[x]: product[x]
        for x in ["prices_per_unit", "units", "description"]
        if x in product.keys() and product[x] is not float("nan")
    }

    transformed = {
        "AmazonProduct": {"name": product["title"], "ASIN": product["asin"]},
        "ProductDetail": {
            "rating": product["rating"],
            "review_numbers": product["review_nb"],
            "price": product["prices_main"],
            "price_per_unit": product["prices_per_unit"],
            "units": product["units"],
            "image_url": product["img"],
            "url": product["url"],
        },
    }

    transformed["ProductDetail"].update(optional_args)
    return transformed

def aliexpress_transformer(product: dict) -> dict:

    transformed = {
        "AliexpressProduct": {"name": product["title"], "ID": product["id"]},
        "ProductDetail": {
            "rating": '',
            "review_numbers": '',
            "price": product["price_current"],
            "price_per_unit": '',
            "units": '',
            "image_url": product["image"],
            "url": '',
            "description": product['title'],
        },
    }
    return transformed


def ebay_scraper(keywords, filename, limit=999999, proxy_limit=10):
    env = os.environ.copy()
    env["EBAY_PROXY_LIMIT"] = str(proxy_limit)
    env["EBAY_LIMIT"] = str(limit)
    with subprocess.Popen(
        [
            "scrapy",
            "crawl",
            "ebay",
            "-o",
            "../{}".format(filename),
            "-a",
            'search={}'.format(keywords),
        ],
        cwd="scraping-ebay",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env=env,
    ) as p, open('ebay_scraper_logs.txt', 'w+') as logfile:
        while p.poll() is None:
            output = p.stdout.readline().decode()
            print(output.strip())
            logfile.write(output)
    return filename


def ebay_transformer(product: dict) -> dict:
    transformed = {
        "EbayProduct": {
            "name": product["Name"],
            "ebay_id": product["Link"].split("/")[-1].split("?")[0],
        },
        "ProductDetail": {
            "price": product.get("Price", ""),
            "location": product.get("Location", ""),
            "description": product.get("Product Details", ""),
            "url": product.get("Link", ""),
            "image_url": product.get("Image", ""),
            "seller": product.get("Seller", ""),
            "seller_url": product.get("Seller Profile", ""),
        }
    }

    transformed["ProductDetail"] = {
        k: v
        for k, v in transformed["ProductDetail"].items()
        if v != ""
    }

    return transformed


def tp_scraper(keywords, filename, limit=999999, proxy_limit=10):
    env = os.environ.copy()
    env["TP_PROXY_LIMIT"] = str(proxy_limit)
    env["TP_LIMIT"] = str(limit)
    with subprocess.Popen(
        [
            "scrapy",
            "crawl",
            "tp",
            "-o",
            "../{}".format(filename),
            "-a",
            'search={}'.format(keywords),
        ],
        cwd="tp-scraper",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env=env,
    ) as p, open('tp_scraper_logs.txt', 'w+') as logfile:
        while p.poll() is None:
            output = p.stdout.readline().decode()
            print(output.strip())
            logfile.write(output)
    return filename


def store_ebay_results(results, search, session=None):
    product_ids = []
    with open(results, 'r') as results_file:
        csvreader = csv.reader(results_file)
        headers = []
        for row in csvreader:
            if len(headers) == 0:
                headers = row
            else:
                product = {
                    headers[i]: row[i]
                    for i in range(len(headers))
                    if row[i] != ""
                }

                transformed_product = ebay_transformer(product)
                ebay_product = EbayProduct(**transformed_product["EbayProduct"])

                session.add(ebay_product)
                session.flush()

                product_detail = ProductDetail(
                    product=ebay_product.id, search=search.id, **transformed_product["ProductDetail"]
                )
                session.add(product_detail)
                session.flush()

                product_ids.append(ebay_product.id)
        session.commit()
    return product_ids


def store_amazon_results(results, search, session=None):
    if not session:
        session = create_session()

    product_ids = []

    for result in results:
        transformed_result = amazon_transformer(result.product)
        product = AmazonProduct(**transformed_result["AmazonProduct"])
        session.add(product)
        session.flush()
        product_ids.append(product.id)

        product_detail = ProductDetail(
            product=product.id, search=search.id, **transformed_result["ProductDetail"]
        )
        session.add(product_detail)
    session.commit()

    return product_ids

def store_aliexpress_results(results, search, session=None):
    if not session:
        session = create_session()

    product_ids = []

    for result in results:
        transformed_result = aliexpress_transformer(result.product)
        product = AliexpressProduct(**transformed_result["AliexpressProduct"])
        session.add(product)
        session.flush()
        product_ids.append(product.id)

        product_detail = ProductDetail(
            product=product.id, search=search.id, **transformed_result["ProductDetail"]
        )
        session.add(product_detail)
    session.commit()

    return product_ids

def store_tp_results(results, search, session=None):
    pass


def update_null_product_details(proxy_limit=10, session=None):
    if not session:
        session = create_session()

    null_product_details = (
        session.query(ProductDetail)
        .filter(ProductDetail.description == None)
        .all()
    )
    products = (
        session.query(AmazonProduct)
        .filter(AmazonProduct.id.in_([x.product for x in null_product_details]))
        .all()
    )
    update_product_details(session, products, null_product_details, proxy_limit=proxy_limit)


def update_product_details(session, products, product_details, amazon_client=None, proxy_limit=10):
    # where products is a SQLALchemy query result
    if amazon_client is None:
        amazon_client = Client(proxy_limit=proxy_limit)
    block_size = 5

    p_map = {
        x.id: x
        for x in products
    }

    pd_map = {
        x.product: x
        for x in product_details
    }

    combined_products = []
    for x in pd_map.keys():
        combined_products.append({
            'name': p_map[x].name,
            'ASIN': p_map[x].ASIN,
            'url': pd_map[x].url
        })

    pd_asin_map = {
        p_map[x.product].ASIN: x
        for x in product_details
    }

    for i in range(int(ceil(len(combined_products) / block_size))):
        end_i = (i + 1) * block_size
        _products = combined_products[
            i * block_size: end_i if end_i < len(products) else len(products)
        ]
        product_details = amazon_client._get_product_details(_products)
        for ASIN, details in product_details.items():
            if "description" in details.keys():
                pd_asin_map[ASIN].description = details['description']
        session.commit()


def get_product_and_pds_from_ids(product_ids, session=None):
    if not session:
        session = create_session()
    product_details = (
        session.query(ProductDetail)
        .filter(ProductDetail.product.in_(product_ids))
        .all()
    )

    products = (
        session.query(AmazonProduct)
        .filter(AmazonProduct.id.in_([x.product for x in product_details]))
        .all()
    )
    return {
        'products': products,
        'product_details': product_details,
    }
