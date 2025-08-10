# Telegram Multi-Feature Bot 🤖

A comprehensive Telegram bot with social networking, price tracking, and utility features built with Python and the `python-telegram-bot` library.

![Bot Features Preview](https://via.placeholder.com/800x400?text=Telegram+Bot+Demo)
_(Consider adding actual screenshots later)_

## 🌟 Key Features

### 💬 Social Features

- **Anonymous Chat System**: Secure, identity-protected messaging
- **User Profiles**:
  - Create/edit profiles with photos
  - Gender/age/location filters
  - Friend/like/block system
- **Advanced Matching**:
  - Distance-based search
  - Last online filtering
  - Gender/age preferences

### 💰 Financial Tools

- **Gold/Dollar Tracker**:
  - Real-time prices from tgju.org and goldpricez.com
  - Price calculator with construction/shop fees
- **Torob.com Price Monitor**:
  - Track product price drops
  - Get alerts when prices hit your target

### 🔧 Utilities

- Multi-language support
- Database-backed user sessions
- Inline query support
- Conversation handlers for complex interactions

## 🛠 Technical Stack

### Core Technologies

- Python 3.10+
- `python-telegram-bot` (v20+)
- SQLAlchemy (ORM)
- BeautifulSoup4 (Web scraping)
- Requests (HTTP client)
- httpx (async http requests)

### Database Schema

- User profiles and relationships
- Chat sessions and messages
- Price tracking history
- Product monitoring

## 🚀 Installation Guide

### Prerequisites

- Python 3.10 or newer
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Basic server setup (for deployment)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/AMirSaLaRG/telegram-bot.git
   cd telegram-bot
   ```
