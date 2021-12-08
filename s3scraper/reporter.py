import csv
from datetime import datetime

from db import create_session
from db import AmazonProduct, AliexpressProduct, EbayProduct, ProductDetail, Search


def create_csv(headers, rows, filename):
    with open(filename, "w+") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(headers)
        for row in rows:
            csv_writer.writerow(
                [
                    p.replace(",", ";")
                    if isinstance(p, str)
                    else p
                    for p in row   
                ]
                if any([
                    "," in str(x) for x in row
                ])
                else row
            )


def get_amazon_products():
    session = create_session()
    amazon_products = session.query(
        AmazonProduct.name,
        AmazonProduct.ASIN,
        ProductDetail.description,
        ProductDetail.rating,
        ProductDetail.review_numbers,
        ProductDetail.price,
        ProductDetail.currency,
        ProductDetail.price_per_unit,
        ProductDetail.units,
        ProductDetail.url,
        ProductDetail.image_url,
        Search.search_params,
        Search.search_date,
    ).filter(
        AmazonProduct.ASIN != None
    ).filter(
        ProductDetail.product == AmazonProduct.id
    ).filter(
        Search.id == ProductDetail.search
    ).all()

    headers = [
        "Product",
        "ID",
        "Description",
        "Rating",
        "No. of Reviews",
        "Main Price",
        "Currency",
        "Price per Unit",
        "Units",
        "URL",
        "Image URL",
        "Search Used",
        "Search Date"
    ]
    return {
        "headers": headers,
        "rows": amazon_products
    }

def get_aliexpress_products():
    session = create_session()
    aliexpress_products = session.query(
        AliexpressProduct.name,
        AliexpressProduct.ID,
        ProductDetail.description,
        ProductDetail.rating,
        ProductDetail.review_numbers,
        ProductDetail.price,
        ProductDetail.currency,
        ProductDetail.price_per_unit,
        ProductDetail.units,
        ProductDetail.url,
        ProductDetail.image_url,
        Search.search_params,
        Search.search_date,
    ).filter(
        AliexpressProduct.ID != None
    ).filter(
        ProductDetail.product == AliexpressProduct.id
    ).filter(
        Search.id == ProductDetail.search
    ).all()

    headers = [
        "Product",
        "ID",
        "Description",
        "Rating",
        "No. of Reviews",
        "Main Price",
        "Currency",
        "Price per Unit",
        "Units",
        "URL",
        "Image URL",
        "Search Used",
        "Search Date"
    ]
    return {
        "headers": headers,
        "rows": aliexpress_products
    }

def get_ebay_products():
    session = create_session()
    ebay_products = session.query(
        EbayProduct.name,
        EbayProduct.ebay_id,
        ProductDetail.description,
        ProductDetail.price,
        ProductDetail.url,
        ProductDetail.image_url,
        ProductDetail.seller,
        ProductDetail.seller_url,
        ProductDetail.location,
        Search.search_params,
        Search.search_date,
    ).filter(
        EbayProduct.ebay_id != None
    ).filter(
        ProductDetail.product == EbayProduct.id
    ).filter(
        Search.id == ProductDetail.search
    ).all()

    headers = [
        "Product",
        "ID",
        "Description",
        "Main Price",
        "URL",
        "Image URL",
        "Seller",
        "Seller URL",
        "Location",
        "Search Used",
        "Search Date"
    ]
    return {
        "headers": headers,
        "rows": ebay_products
    }


def export_all_amazon():
    data = get_amazon_products()
    create_csv(
        headers=data["headers"],
        rows=data["rows"],
        filename="amazon_all-{}.csv".format(datetime.now().strftime("%m-%d-%Y"))
    )

def export_all_aliexpress():
    data = get_aliexpress_products()
    create_csv(
        headers=data["headers"],
        rows=data["rows"],
        filename="aliexpress_all-{}.csv".format(datetime.now().strftime("%m-%d-%Y"))
    )

def export_all_ebay():
    data = get_ebay_products()
    create_csv(
        headers=data["headers"],
        rows=data["rows"],
        filename="ebay_all-{}.csv".format(datetime.now().strftime("%m-%d-%Y"))
    )


def export_all_tp():
    pass

def export_unified():
    header_order = [
        "Product",
        "ID",
        "Description",
        "Main Price",
        "URL",
        "Image URL",
        "Location",
        "Rating",
        "No. of Reviews",
        "Currency",
        "Price per Unit",
        "Units",
        "Seller",
        "Seller URL",
        "Search Used",
        "Search Date",
    ]
    filename = "export_all-{}.csv".format(datetime.now().strftime("%m-%d-%Y"))

    with open(filename, "w+") as csvfile:
        print("NOTICE: Exporting to {}".format(filename))
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(header_order)

    data_functions = [
        get_amazon_products,
        get_ebay_products
    ]

    block_size = 500
    for data_function in data_functions:
        data = data_function()
        rows = []
        for row in data["rows"]:
            row_dict = {
                data["headers"][i]: row[i]
                for i in range(len(data["headers"]))
            }
            output_row = [
                row_dict.get(header, "") for header in header_order
            ]
            rows.append(output_row)
            if len(rows) >= block_size:
                with open(filename, "a") as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',')
                    csv_writer.writerows(rows)
                rows = []
        with open(filename, "a") as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            csv_writer.writerows(rows)


if __name__ == "__main__":
    export_all_amazon()
