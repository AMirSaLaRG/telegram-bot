# My Awesome Telegram Bot

---

## Description
This Telegram bot provides features like anonymous chat, random user matching, and real-time price tracking for gold/dollar and products from Torob.com. It's designed to offer a unique social interaction experience alongside practical utility.

---

## Features
* **Anonymous Chat:** Connect with other users without revealing identities.
* **Random Chat:** Find new chat partners quickly.
* **User Profiles:** Create and manage your profile (name, age, gender, location, photo).
* **Gold & Dollar Price Tracker:** Get live prices from `tgju.org` and `goldpricez.com`.
* **Torob Price Tracker:** Track specific products on Torob.com and get notified of best offers.
* **Database:** Uses SQLite with SQLAlchemy for robust data storage.

---

## Technologies Used
* Python 3.x
* `python-telegram-bot`
* SQLAlchemy
* BeautifulSoup4 (for web scraping)
* Requests
* `python-dotenv` (Recommended for environment variables)

---

## Setup & Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-bot-repo.git](https://github.com/your-username/your-bot-repo.git)
    cd your-bot-repo
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    * **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    * **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (If you don't have `requirements.txt` yet, create it with: `pip freeze > requirements.txt`)
4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory:
    ```
    BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
    # Add other sensitive info like API keys if you add them later
    ```

---

## How to Run
```bash
python main.py