import logging
import math
from dotenv import load_dotenv


from telegram import (Update, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, )
from telegram.error import BadRequest
from telegram.ext import (filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler)

from bot.handlers.gold_dollar_report import GoldDollarReport
from bot.handlers.torob_interact import TorobInteract
from bot.handlers.telegram_conversations import Calculator, TorobConversation
from bot.handlers.profile import Profile
from bot.handlers.filter import Filter

from bot.db.database import GoldPriceDatabase, UserDatabase, iran_cities_fa, ChatDatabase, TorobDb
from bot.handlers.telegram_chat_handler import UserMessage
from bot.handlers.start import Start
import os
from datetime import datetime
from functools import wraps
from bot.utils.en import Messages


load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')


divider = Messages.DIVIDER

#WHAT IS THIS TWO FOR
os.makedirs("../profiles", exist_ok=True)

# Ensure directory exists
os.makedirs("../profiles", exist_ok=True)

user_message = UserMessage()

#____________________ commandhandlers______________________________
start = Start()
gold_dollar_report = GoldDollarReport()
torob_interact = TorobInteract()
bot_filter = Filter()
# ___________________conversations_________________________________
profile = Profile()
calculator = Calculator()
torob_conversation = TorobConversation()
# ___________________data_bases_________________________________

gold_db = GoldPriceDatabase()
user_db = UserDatabase()
chat_db = ChatDatabase()
torob_db = TorobDb()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# ___________________________________________________________________________________________
#                             inline keys
# ___________________________________________________________________________________________

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all inline button callbacks.
    Routes to specific functions based on the callback data prefix.
    """
    query = update.callback_query
    await query.answer()

    await bot_filter.buttons(update, context)
    await user_message.buttons_set(update, context)
    await torob_interact.button(update, context)
    await gold_dollar_report.button(update, context)
    await profile.buttons(update, context)


# _______________________________________________________________________________
# ________________________Robot run and handlers_________________________________
# _______________________________________________________________________________

if __name__ == "__main__":
    # Initialize the Telegram Application Builder with bot token and concurrent updates.
    application = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

    # Create Handlers for various commands and message types.
    start_handler = start.handler()
    advance_search_handler = bot_filter.advance_search_handler()
    gold_dollar_handler = gold_dollar_report.handler()
    torob_handlers = torob_interact.handlers()
    my_profile = CommandHandler("profile", profile.show_my_profile)
    # Inline button handler
    buttons_handler = CallbackQueryHandler(buttons)

    # Add handlers to the application.
    application.add_handler(start_handler)
    application.add_handler(advance_search_handler)
    application.add_handler(gold_dollar_handler)
    application.add_handlers(torob_handlers)

    application.add_handler(calculator.get_calculated_price_conversation_handler())
    application.add_handlers(profile.get_all_handlers())
    application.add_handlers(torob_conversation.get_all_handlers())
    application.add_handler(my_profile)
    application.add_handlers(user_message.message_handlers())
    application.add_handler(buttons_handler)

    application.run_polling()

# _______________________________________________________________________________
# ___________________________Problems & checks___________________________________
# _______________________________________________________________________________

