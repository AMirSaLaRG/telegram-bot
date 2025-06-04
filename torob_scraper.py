import time

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError, RequestException
#can be a class
import random
from data_base import TorobDb





class TorobScraper:
    def __init__(self):
        self.url = None
        self.my_price = 99999999999999999999
        self.name = None
        self.db = TorobDb()

    def torop_price_format_clear(self, text:str) ->int:
        price = text.replace("٫", "")
        price = price.split()[0]
        price = int(price)
        return price

    def scrap_lowest_price_torop(self):
        """Get torop page check the lowest price in recommend of torop and top 5 then returns the lowest price"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        ]
        random_agent = random.choice(user_agents)
        print(random_agent)
        headers = {
            'User-Agent': random_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://torob.com/',
        }
        session = requests.Session()
        session.headers.update(headers)
        try:
            response = session.get(self.url, timeout=10)
            response.raise_for_status()
        except HTTPError as http_err:
            if response.status_code == 490:
                print("Torob blocked the request (HTTP 490)")
                return None
            else:
                print(f"HTTP Error occurred: {http_err}")
                return None
        except RequestException as req_err:
            print(f"Request failed (Connection/Timeout/SSL Error): {req_err}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        else:
            my_html = response.text

            soup = BeautifulSoup(my_html, "html.parser")

            box_lower_price_tag = soup.select_one(".Showcase_buy_box__q4cpD")
            seller_price_tag = box_lower_price_tag.select(".Showcase_buy_box_text__otYW_")
            # seller = seller_price_tag[0].getText()
            price_torop_recommend = seller_price_tag[1].getText()
            price_torop_recommend = self.torop_price_format_clear(price_torop_recommend)

            top_5_prices_tag = soup.select(".price-credit a")
            top_5_price = [self.torop_price_format_clear(tag.getText()) for tag in top_5_prices_tag]
            lowest_top_5 = min(top_5_price)

            if lowest_top_5 < price_torop_recommend:
                return lowest_top_5
            else:
                return price_torop_recommend

    def the_good_offer(self, max_retries=11, retry_count=0):
        if max_retries == retry_count:
            print('got blocked more than 10 times')
            return None
        best_price = self.scrap_lowest_price_torop()
        print(best_price)
        if best_price is not None:
            if best_price <= self.my_price:
                return best_price
            else:
                return None

        else:
            time.sleep(3)
            return self.the_good_offer(max_retries, retry_count+1)


def main():
    torob_scraper = TorobScraper()
    torob_scraper.url = "https://torob.com/p/f53c80e9-230e-47a6-83ec-37bc376a3d15/microsoft-surface-laptop-6-ultra-5-135h-16-256-int-135-inch/"
    torob_scraper.my_price = 9999999999
    good_offer = torob_scraper.the_good_offer()

    if good_offer:
        print(good_offer)


if __name__ == "__main__":
    main()

