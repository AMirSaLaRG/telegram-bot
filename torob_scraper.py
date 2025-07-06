import logging
import time
from typing import Optional, List, Type

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

    def add_item(self, user_id, item_name, url, preferred_price)->bool:
        """

        :param user_id: id of who wants the scrap
        :param item_name: name of item
        :param url: url of the item in torob site
        :param preferred_price: the highest price the person need it to be
        :return: True if item added, False if it did not add
        """
        try:
            preferred_price= float(preferred_price)
        except Exception as e:
            print(f'price format: {e}')

        if self.db.add_item(user_id, preferred_price, url, item_name):
            return True
        else:
            return False


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

    def the_good_offer(self ,max_retries=11, retry_count=0):
        if max_retries == retry_count:
            logging.warning(f"Max retries reached for URL: {self.url}")
            return None
        try:
            best_price = self.scrap_lowest_price_torop()
            if best_price is None:
                time.sleep(2)
                return self.the_good_offer(max_retries, retry_count + 1)
            return best_price
        except Exception as e:
            logging.error(f"Scraping error: {e}")
            return None

    def scrap_user_items(self, user_id:int) -> bool:
        """
        this will scrap the users interested items and fill the database checked items
        :param user_id: id of user who want check items
        :return: bool
        """
        items = self.db.get_user_items(user_id)
        added = 0
        if items:
            for item in items:
                self.url = item.torob_url
                best_price = self.the_good_offer()
                if best_price:
                    try:
                        self.db.add_check(item.item_id, float(best_price))
                        added += 1
                    except Exception as e:
                        print(f'could not add to check db : {e}')
            if added != 0:
                print(f'{added} item from {len(items)} checked for new price')
                return True
            else:
                print('could not update check')
                return False
        print('database is emty')
        return False

    def scrap_all_users_items(self):
        users = self.db.get_users_with_items()
        if users:
            for user in users:
                self.scrap_user_items(user)



def main():
    torob_scraper = TorobScraper()
    # torob_scraper.url = "https://torob.com/p/0ac4bc23-fe13-491d-b404-33cc95b9a2df/%D9%85%DB%8C%D8%B2-%D9%86%D8%A7%D9%87%D8%A7%D8%B1-%D8%AE%D9%88%D8%B1%DB%8C-4%D9%86%D9%81%D8%B1%D9%87-%DA%86%D9%88%D8%A8%DB%8C-%DA%A9%D9%85%D8%AC%D8%A7-%D8%AC%D8%AF%DB%8C%D8%AF/"
    # torob_scraper.my_price = 9999999999
    # good_offer = torob_scraper.the_good_offer()
    #
    # if good_offer:
    #     print(good_offer)
    torob_scraper.scrap_all_users_items()

if __name__ == "__main__":
    main()

