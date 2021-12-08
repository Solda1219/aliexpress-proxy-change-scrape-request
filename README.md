# MEDSCRAPER

Scraper for the italian versions of Amazon, Ebay, and Alibaba.

## Running the Scraper

1. Install `python3` on your system
2. Install the requirements with `pip3`

```shell
pip3 install -r requirements.txt
```

3. Run the scraper

```shell
python main.py
```

### Search

Searching will give you three options: site to scrape, search limit (number of results to get), and proxy limit (number of proxies to use).

The Amazon Scraper also gives you an additional option to defer fetching product details (which are sourced from the individual product pages).

### Update Product Details

The Amazon scraper gives you the option to update the product details for items in the database with no descriptions. This operation takes a long time (hence its separation from search).

### Export CSV

You can export the products for each site individually (by first choosing to use that specific scraper), or you can choose the third option on the CLI:

```shell
******************************
Amazon/Ebay/Alibaba Product Scraper
******************************
1. Scrape Amazon
2. Scrape Ebay
3. Export all scraped products
```

This will create a CSV with all the products scraped from all sites on a unified sheet. There will be blank columns because of information available on one site but not the others. The CSV will be named `export_all-MM-DD-YYYY.csv` where `MM-DD-YYYY` is the current date.

## Price Formatting

### Amazon

Products on Amazon might have multiple prices due to multiple SKUs. In which case the exported CSV will list down all the available prices for the product.

### Ebay

Products on Ebay might have two prices, the current bid offer and the Buy Now price. If so, the exported CSV will list down the price as `XX.XX / YY.YY` where the first price (`XX.XX`) is the bid offer while the second price (`YY.YY`) is the Buy Now price.

## Notes

* Proxies are used to avoid being blocked/banned
* Debug logs for the ebay scraper are generated as `ebay_scraper_logs.txt`
* To debug Scrapy code, insert this snippet

```python
from scrapy.shell import inspect_response
inspect_response(response, self)
```
