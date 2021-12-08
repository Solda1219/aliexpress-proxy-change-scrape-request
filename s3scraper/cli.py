import os
from datetime import datetime

from db import create_session
from reporter import export_all_amazon, export_all_aliexpress, export_all_ebay, export_unified, export_all_tp
from scraper import scrape
from utils import (update_null_product_details)
from amazonscraper.logger import AmazonLogPrinter
from aliexpress.logger import AliexpressLogPrinter


def amazon_cli(session=None):
    print("*" * 30)
    print("Amazon Product Scraper")
    print("*" * 30)
    action = input(
        "1. Search\n2. Fetch product details\n3. Export scraped products\n\nPlease input number of action you want to do: "
    )

    action = int(action)
    if not session:
        session = create_session()
    if action == 1:
        get_details = input(
            "Do you want to scrape product details? Please note that this takes a long time to complete so it's recommended to \
run search then get product details as a separate command: [y/n]: "
        )

        search_limit = input("Set search limit (input -1 to uncap): ")
        search_limit = int(search_limit)

        proxy_limit = input("Set number of proxies to use [Recommended: 10]: ")
        proxy_limit = int(proxy_limit)

        keywords = input("Input search phrase: ")

        search_params = {"keywords": keywords, "limit": search_limit}
        scrape(
            site="amazon",
            search_params=search_params,
            proxy_limit=proxy_limit,
            client=None,
            get_pds=get_details.lower() == "y",
        )
        AmazonLogPrinter.export("amazon_logs.txt")
    if action == 2:
        proceed = input(
            "This fetches the product details for products in the database currently w/o that info, do you want to proceed? [y/n]: "
        )
        if proceed.lower() == "y":

            proxy_limit = input("Set number of proxies to use [Recommended: 10]: ")
            proxy_limit = int(proxy_limit)
            update_null_product_details(proxy_limit=proxy_limit, session=session)
            AmazonLogPrinter.export("amazon_logs.txt")
    if action == 3:
        export = input(
            "This exports all the product information currently on the database, do you want to proceed? [y/n]: "
        )
        if export.lower() == "y":
            export_all_amazon()


def aliexpress_cli(session=None):
    print("*" * 30)
    print("ALiexperss Product Scraper")
    print("*" * 30)
    action = input(
        "1. Search\n2. Fetch product details\n3. Export scraped products\n\nPlease input number of action you want to do: "
    )

    action = int(action)
    if not session:
        session = create_session()
    if action == 1:
        get_details = input(
            "Do you want to scrape product details? Please note that this takes a long time to complete so it's recommended to \
run search then get product details as a separate command: [y/n]: "
        )

        search_limit = input("Set search limit (input -1 to uncap): ")
        search_limit = int(search_limit)

        proxy_limit = input("Set number of proxies to use [Recommended: 10]: ")
        proxy_limit = int(proxy_limit)

        keywords = input("Input search phrase: ")

        search_params = {"keywords": keywords, "limit": search_limit}
        scrape(
            site="aliexpress",
            search_params=search_params,
            proxy_limit=proxy_limit,
            client=None,
            get_pds=get_details.lower() == "y",
        )
        AliexpressLogPrinter.export("aliexpress_logs.txt")
    if action == 2:
        proceed = input(
            "This fetches the product details for products in the database currently w/o that info, do you want to proceed? [y/n]: "
        )
        if proceed.lower() == "y":

            proxy_limit = input("Set number of proxies to use [Recommended: 10]: ")
            proxy_limit = int(proxy_limit)
            update_null_product_details(proxy_limit=proxy_limit, session=session)
            AliexpressLogPrinter.export("aliexpress_logs.txt")
    if action == 3:
        export = input(
            "This exports all the product information currently on the database, do you want to proceed? [y/n]: "
        )
        if export.lower() == "y":
            export_all_aliexpress()

def ebay_cli(session=None):
    print("*" * 30)
    print("Ebay Product Scraper")
    print("*" * 30)

    action = input(
        "1. Search\n2. Export scraped products\n\nPlease input number of action you want to do: "
    )

    action = int(action.strip())

    if action == 1:
        keywords = input("Input search phrase: ")

        search_limit = input("Set search limit (input -1 to uncap): ")
        search_limit = int(search_limit.strip())
        if search_limit == -1:
            search_limit = 999999

        proxy_limit = input("Set number of proxies to use [Recommended: 10]: ")
        proxy_limit = int(proxy_limit.strip())

        filename = "{}_{}.csv".format(keywords.replace(" ", "-").lower(), datetime.now().strftime("%m-%d-%Y"))
        print("NOTICE: Saving scrape results in {}".format(filename))
        filepath = "{}".format(filename)
        if os.path.exists(filepath):
            cont = input("WARNING: This will overwrite the existing file, continue? [y/n]")
            cont = cont.strip().lower()
            if cont != "y":
                print("Exiting program")
                exit
            else:
                os.remove(filepath)
        scrape(
            site="ebay",
            search_params={
                "keywords": keywords,
                "limit": search_limit,
                "filename": filename,
            },
            proxy_limit=proxy_limit
        )
    elif action == 2:
        export = input(
            "This exports all the product information currently on the database, do you want to proceed? [y/n]: "
        )
        if export.lower() == "y":
            export_all_ebay()


def tp_cli(session=None):
    print("*" * 30)
    print("Trovaprezzi Product Scraper")
    print("*" * 30)

    action = input(
        "1. Search\n2. Export scraped products\n\nPlease input number of action you want to do: "
    )

    action = int(action.strip())

    if action == 1:
        keywords = input("Input search phrase: ")

        search_limit = input("Set search limit (input -1 to uncap): ")
        search_limit = int(search_limit.strip())
        if search_limit == -1:
            search_limit = 999999

        proxy_limit = input("Set number of proxies to use [Recommended: 10]: ")
        proxy_limit = int(proxy_limit.strip())

        filename = "tp-{}_{}.csv".format(keywords.replace(" ", "-").lower(), datetime.now().strftime("%m-%d-%Y"))
        print("NOTICE: Saving scrape results in {}".format(filename))
        filepath = "{}".format(filename)
        if os.path.exists(filepath):
            cont = input("WARNING: This will overwrite the existing file, continue? [y/n]")
            cont = cont.strip().lower()
            if cont != "y":
                print("Exiting program")
                exit
            else:
                os.remove(filepath)
        scrape(
            site="tp",
            search_params={
                "keywords": keywords,
                "limit": search_limit,
                "filename": filename,
            },
            proxy_limit=proxy_limit
        )
    elif action == 2:
        export = input(
            "This exports all the product information currently on the database, do you want to proceed? [y/n]: "
        )
        if export.lower() == "y":
            export_all_tp()


def main_cli(session=None):
    print("*" * 30)
    print("Amazon/Ebay/Trovaprezzi Product Scraper")
    print("*" * 30)
    action = input(
        "1. Scrape Amazon\n\
2. Scrape Aliexpress\n\
3. Scrape Ebay\n\
4. Scrape Trovaprezzi\n\
5. Export all scraped products\n\
\nPlease input number of action you want to do: "
    )
    action = int(action.strip())
    if action == 1:
        amazon_cli(session)
    if action == 2:
        aliexpress_cli(session)
    if action == 3:
        ebay_cli(session)
    if action == 4:
        tp_cli(session)
    if action == 5:
        export_unified()
