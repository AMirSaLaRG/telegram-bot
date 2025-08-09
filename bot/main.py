import logging

import telegram
from dotenv import load_dotenv


from telegram import (Update, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, )

from telegram.ext import (filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler, InlineQueryHandler)


from bot.handlers.gold_dollar_report import GoldDollarReport
from bot.handlers.torob_interact import TorobInteract
from bot.handlers.telegram_conversations import Calculator, TorobConversation
from bot.handlers.profile import Profile
from bot.handlers.filter import Filter
from bot.handlers.relationship import RelationshipHandler
from bot.handlers.show_cases import ShowCases

from bot.db.database import GoldPriceDatabase, UserDatabase, iran_cities_fa, ChatDatabase, TorobDb
from bot.handlers.telegram_chat_handler import UserMessage
from bot.handlers.start import Start
import os
import warnings

from bot.handlers.intraction import track_user_interaction
#the error per_message=True  i think that will be not issue not sure though
from telegram.warnings import PTBUserWarning
from bot.utils.messages_manager import messages as msg
# messages = msg(language=context.user_data['lan'])

warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*per_message=False.*")


#todo moshakhas beshe in user_data haii ke add kardam kojaha add mishe kojaha estefade mishe



#todo bara static cardane searcha mishe ye table mesle user tolid kard ke searcharo ba id generate save mikone bad to query mass mide

#todo main problem in scripting the site the robot get freez kinda until it get all

messages = msg()
load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
divider = messages.DIVIDER


# Ensure directory exists
os.makedirs("../profiles", exist_ok=True)

user_message = UserMessage()

#____________________ commandhandlers______________________________
start = Start()
gold_dollar_report = GoldDollarReport()
torob_interact = TorobInteract()
bot_filter = Filter()
rel = RelationshipHandler()
show_case = ShowCases()
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
#                             inline Query
# ___________________________________________________________________________________________
@track_user_interaction
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles inline queries to show user profiles in a scrollable interface.
    """
    message = msg()
    user_id = update.inline_query.from_user.id

    query = update.inline_query.query.strip().lower()

    #gettingfilteredppl
    if query == message.QUERY_PATTERN_FILTERED_PPL:

        ppl = context.user_data.get("selected_users", None)
        if ppl:
            await show_case.inline_show_selected_users(update, context, ppl)

    #todo in as filter migire na az show case fitler as show case migire


    # await update.inline_query.answer(results, cache_time=0)

# ___________________________________________________________________________________________
#                             inline keys
# ___________________________________________________________________________________________
@track_user_interaction
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all inline button callbacks.
    Routes to specific functions based on the callback data prefix.
    """
    query = update.callback_query
    try:
        await query.answer()

        await bot_filter.buttons(update, context)

        await user_message.buttons_set(update, context)
        await rel.buttons(update, context)
        await profile.buttons(update, context)


        await torob_interact.button(update, context)
        await gold_dollar_report.button(update, context)
        await show_case.buttons(update, context)
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            # Query expired, ignore it
            pass
        else:
            raise

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

    # Inline button handler
    buttons_handler = CallbackQueryHandler(buttons)

    # Add handlers to the application.
    application.add_handler(start_handler)
    application.add_handler(advance_search_handler)
    application.add_handler(gold_dollar_handler)
    application.add_handlers(torob_handlers)

    application.add_handler(InlineQueryHandler(handle_inline_query))

    application.add_handler(calculator.get_calculated_price_conversation_handler())
    application.add_handlers(profile.get_all_handlers())
    application.add_handlers(torob_conversation.get_all_handlers())
    application.add_handlers(user_message.message_handlers())
    application.add_handler(buttons_handler)

    application.run_polling()

# _______________________________________________________________________________
# ___________________________Problems & checks___________________________________
# _______________________________________________________________________________

