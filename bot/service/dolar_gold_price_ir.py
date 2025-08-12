# import requests
import httpx
import asyncio
from bs4 import BeautifulSoup
import time
from datetime import datetime
import random


class CheckSitePrice:
    """
    A class for scraping gold and dollar prices from specified websites.
    It fetches prices from Iranian (tgju.org) and international (goldpricez.com) sources.
    """

    def __init__(self):
        """
        Initializes the CheckSitePrice with URLs for Iranian and international
        price sites, and sets up HTTP headers for requests.
        """
        self.ir_site = "https://www.tgju.org/"
        self.int_site = "https://goldpricez.com/us/18k/gram#navbar"
        # Standard HTTP headers to mimic a web browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # Initialize a requests session with the defined headers
        # self.session = requests.Session()
        # self.session.headers.update(self.headers)

    async def safe_get(self, url, client):
        """
        Performs a safe HTTP GET request to the given URL with a random delay.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The content of the response as text if successful, None otherwise.
        """
        try:
            # Introduce a random delay to avoid being flagged as a bot
            await asyncio.sleep(random.uniform(1, 3))
            response = await client.get(url, headers=self.headers)
            # Raise an HTTPError for bad responses (4xx or 5xx)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def get_ir_gold_dollar(self, client):
        """
        Fetches the current 18K gold price in Iranian Rial and the US Dollar to Iranian Rial exchange rate
        from the specified Iranian financial website.

        Returns:
            tuple: A tuple containing:
                   - str: 18K gold price in Iranian Rial.
                   - str: US Dollar to Iranian Rial exchange rate.
                   - datetime: The timestamp when the data was fetched.
                   Returns None for all if fetching fails.
        """
        html_iran = await self.safe_get(self.ir_site, client)
        if html_iran:
            soup = BeautifulSoup(html_iran, "html.parser")
            # Select the element containing the 18K gold price
            price_iran_18k_gold = soup.select_one("#l-geram18 .info-price").getText()
            # Select the element containing the Dollar to Rial exchange rate
            price_dollar_rial = soup.select_one(
                "#l-price_dollar_rl .info-price"
            ).getText()
            print(f"Iran 18K Gold: {price_iran_18k_gold}")
            print(f"Dollar to Rial: {price_dollar_rial}")
            return price_iran_18k_gold, price_dollar_rial, datetime.now()
        return None, None, None

    async def get_int_gold_to_dollar_to_rial(self, client, price_dollar_rial=None):
        """
        Fetches the international 18K gold price in USD and converts it to Iranian Rial
        using an optionally provided dollar-to-rial exchange rate.

        Args:
            price_dollar_rial (str, optional): The current US Dollar to Iranian Rial exchange rate.
                                               If None, it will prompt for input.

        Returns:
            tuple: A tuple containing:
                   - str: International 18K gold price in USD.
                   - float: International 18K gold price converted to Iranian Rial.
                   - datetime: The timestamp when the data was fetched.
                   Returns None for all if fetching fails.
        """
        html_world = await self.safe_get(self.int_site, client)
        if html_world:
            soup = BeautifulSoup(html_world, "html.parser")
            # Select the element containing the international 18K gold price in USD
            price_element = soup.select_one(
                'p span[aria-label="Current 18-Karat Gold Price per Gram in USD"]'
            )
            if price_element:
                # Extract text, strip whitespace, and remove '$' sign
                price_usd_18k_gold = price_element.getText().strip().replace("$", "")
                print(f"International 18K Gold (USD): {price_usd_18k_gold}")

                int_gold_rial = None
                if price_dollar_rial:
                    # Convert USD gold price to Rial using the provided exchange rate
                    int_gold_rial = float(price_usd_18k_gold) * float(
                        price_dollar_rial.replace(",", "")
                    )
                # else:
                #     # If no exchange rate is provided, ask the user
                #     price_dollar_rial = input("plz insert price of dollar in Rial")
                #     int_gold_rial = float(price_usd_18k_gold) * float(price_dollar_rial.replace(',', ''))
                #     print(f"International 18K Gold (Rial): {int_gold_rial}")
                return price_usd_18k_gold, int_gold_rial, datetime.now()
        return None, None, None

    async def get_public_ip(self):
        """
        Fetches the public IP address of the machine running the script.
        """
        try:
            async with httpx.AsyncClient() as client:
                ip = await client.get("https://api.ipify.org?format=json")
                ip = ip.json().get("ip", "Unknown")
        except Exception:
            ip = "Unknown"

        print(f"Your public IP is: {ip}")
        return ip


async def main():
    """
    Main asynchronous function to run the price checking operations.
    """
    robot_checker = CheckSitePrice()

    # Use httpx.AsyncClient as a context manager for the entire session
    async with httpx.AsyncClient() as client:
        # Fetch Iranian gold and dollar prices
        (
            gold_ir_price,
            dollar_ir_price,
            time_ir_checked,
        ) = await robot_checker.get_ir_gold_dollar(client)
        # Fetch international gold price and convert to Rial
        (
            gold_int_price,
            gold_int_to_rial_price,
            time_int_checked,
        ) = await robot_checker.get_int_gold_to_dollar_to_rial(
            client, price_dollar_rial=dollar_ir_price
        )

    # Print all fetched prices
    print(gold_ir_price, dollar_ir_price, gold_int_price, gold_int_to_rial_price)
    # Get and print the public IP (uses a separate client for simplicity)
    await robot_checker.get_public_ip()


# Entry point for the script
if __name__ == "__main__":
    asyncio.run(main())
