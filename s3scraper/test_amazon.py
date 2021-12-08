import unittest
from scraper import scrape

class TestAmazonScrape(unittest.TestCase):
    def test_search(self):
        '''
        Search for "proseti anca" and get five results
        '''
        search_params = {
            "keywords": "proseti anca",
            "limit": 5
        }
        results = scrape("amazon", search_params)
        self.assertEqual(len(results), 5)
    
        # test saving to database


if __name__ == '__main__':
    unittest.main()
