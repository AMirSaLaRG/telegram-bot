import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import random

class CheckSitePrice:
    def __init__(self):
        self.ir_site =  "https://www.tgju.org/"
        self.int_site = "https://goldpricez.com/us/18k/gram#navbar"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def safe_get(self, url):
        try:
            time.sleep(random.uniform(1, 3))
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_ir_gold_dollar(self):
        html_iran = self.safe_get(self.ir_site)
        if html_iran:
            # todo akharin zaman update / get it from https://www.estjt.ir/
            soup = BeautifulSoup(html_iran, "html.parser")
            price_iran_18k_gold = soup.select_one("#l-geram18 .info-price").getText()
            price_dollar_rial = soup.select_one("#l-price_dollar_rl .info-price").getText()
            print(f"Iran 18K Gold: {price_iran_18k_gold}")
            print(f"Dollar to Rial: {price_dollar_rial}")
            return price_iran_18k_gold, price_dollar_rial, datetime.now()

    def get_int_gold_to_dollar_to_rial(self, price_dollar_rial=None):
        html_world = self.safe_get(self.int_site)
        if html_world:
            # todo akharin zaman update
            soup = BeautifulSoup(html_world, "html.parser")
            price_element = soup.select_one('p span[aria-label="Current 18-Karat Gold Price per Gram in USD"]')
            if price_element:
                price_usd_18k_gold = price_element.getText().strip().replace("$", "")
                print(f"International 18K Gold (USD): {price_usd_18k_gold}")
                if price_dollar_rial:
                    int_gold_rial = float(price_usd_18k_gold) * float(price_dollar_rial.replace(',', ''))
                else:
                    price_dollar_rial = input("plz insert price of dollar in Rial")
                    int_gold_rial = float(price_usd_18k_gold) * float(price_dollar_rial.replace(',', ''))
                    print(f"International 18K Gold (Rial):"
                          f" {int_gold_rial}")
            #todo check if this works
                return price_usd_18k_gold, int_gold_rial, datetime.now()

    def get_public_ip(self):
        try:
            ip = requests.get('https://api.ipify.org?format=json').json()
        except:
            ip =  "Unknown"

        print(f"Your public IP is: {ip}")
        return ip


def main():
    robot_checker = CheckSitePrice()
    gold_ir_price, dollar_ir_price, time_ir_checked = robot_checker.get_ir_gold_dollar()
    gold_int_price, gold_int_to_rial_price, time_int_checked = robot_checker.get_int_gold_to_dollar_to_rial(price_dollar_rial=dollar_ir_price)
    print(gold_ir_price, dollar_ir_price, gold_int_price, gold_int_to_rial_price)
    robot_checker.get_public_ip()



if __name__ == "__main__":
    main()

