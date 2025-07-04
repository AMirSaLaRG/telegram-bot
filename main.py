import logging
import math
from dotenv import load_dotenv
from xmlrpc.client import DateTime

from telegram import (Update, InlineQueryResultArticle,
                      InputTextMessageContent, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, ReplyKeyboardRemove, MessageEntity, )
from telegram.error import BadRequest
from telegram.ext import (InlineQueryHandler, filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler,
                          ConversationHandler)
from telegram_conversations import Profile, Calculator, TorobConversation

from data_base import GoldPriceDatabase, UserDatabase, iran_cities_fa, ChatDatabase, TorobDb
from telegram_chat_handler import UserMessage
import json
import os
from datetime import datetime, timedelta
from functools import wraps



load_dotenv()
divider = '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️'
# todo read about inline commands @bot etc and use it
# todo add a handler at top for each interaction with bot get trigger to make user data and user session and etc..
# todo handle some errors in advance chat likebeing emty in profiles
# todo For the filter handling in main.py, you could create a FilterHandler class:
os.makedirs("profiles", exist_ok=True)

# Ensure directory exists
os.makedirs("profiles", exist_ok=True)

user_message = UserMessage()

# todo put a place for all commands and queries
# anonymous_chat.start_command = 'anom_chat'
# anonymous_msg.start_command = 'anom_message'
#

# todo each act in robot update user last online
# ___________________conversations_________________________________
profile = Profile()
calculator = Calculator()
torob_conversation = TorobConversation()
# ___________________data_bases_________________________________
# todo make it one db with two table (already is xD)
# todo make a postoger db engine
gold_db = GoldPriceDatabase()
user_db = UserDatabase()
chat_db = ChatDatabase()
torob_db = TorobDb()

# todo make a tab to check divar or digikala or shapoor (web scraping)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# ___________________________________________________________________________________________
#                             Robot initiator
# ___________________________________________________________________________________________
async def interact(update_query, context: ContextTypes.DEFAULT_TYPE):
    """
        This handler activates for almost any user interaction.
        It ensures the user's session exists and updates their last_online status.
        """
    if hasattr(update_query, 'effective_user'):
        user_id = update_query.effective_user.id

    elif hasattr(update_query, 'from_user'):
        user_id = update_query.from_user.id
    else:
        print('what is going on in interact')
        user_id = ""

    chat_db.create_user_session(user_id)
    context.user_data['user_id'] = user_id
    context.user_data['last_online'] = datetime.now
    user_db.add_or_update_user(user_id, context.user_data)


# as decorator
def track_user_interaction(func):
    """
    Decorator to handle user session tracking and last online updates.
    Automatically extracts user ID and updates user data before calling the original function.
    """

    @wraps(func)
    async def wrapper(update_query, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Extract user ID from different update types
        if hasattr(update_query, 'effective_user'):
            user_id = update_query.effective_user.id
        elif hasattr(update_query, 'from_user'):
            user_id = update_query.from_user.id
        else:
            print('Warning: Could not determine user ID in track_user_interaction')
            user_id = None

        # Only proceed with tracking if we got a user ID
        if user_id:
            chat_db.create_user_session(user_id)
            context.user_data['user_id'] = user_id
            context.user_data['last_online'] = datetime.now()
            user_db.add_or_update_user(user_id, context.user_data)

        # Call the original handler function
        return await func(update_query, context, *args, **kwargs)

    return wrapper


# todo need to be start over after parts maybe change handler to be not only command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    Initializes user session and displays the main keyboard based on user profile existence.
    """
    await interact(update, context)
    user_db.get_user_data(update.effective_user.id, context.user_data)
    if context.user_data['name']:
        keyboard = [
            [KeyboardButton("ChaT")],
            [
                KeyboardButton("Torob price check"),
                KeyboardButton("Gold & Dollar"),

            ],
            [
                KeyboardButton('/profile')
            ]

        ]
    else:
        keyboard = [
            [KeyboardButton("ChaT")],
            [
                KeyboardButton("Torob price check"),
                KeyboardButton("Gold & Dollar"),

            ],
            [
                KeyboardButton(f'/{profile.create_commend}')
            ]

        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'start',
        reply_markup=reply_markup
    )


# ___________________________________________________________________________________________
#                             Chat initiator
# ___________________________________________________________________________________________

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the 'ChaT' button.
    Displays options related to chat functionalities (random, anonymous, advanced search).
    """
    await interact(update, context)
    keyboard = [
        [KeyboardButton("Random chat")],
        [
            KeyboardButton(f'/{user_message.command_create_anon_chat}'),
            KeyboardButton(f'/{user_message.command_create_anon_msg}')
        ],
        [KeyboardButton('Advance Search')],
        [KeyboardButton('/start')]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='What you looking for?',
        reply_markup=reply_markup,
    )


async def advance_search(update: Update, context:
ContextTypes.DEFAULT_TYPE):
    """
    Initiates the advanced search filter selection.
    Presents inline buttons for various filtering options (Distance, Last Online, Gender, Age, Cities).
    """
    await interact(update, context)

    user_filter = {}
    keyboard = [
        [
            InlineKeyboardButton("Distance", callback_data='A_F: Dis'),
            InlineKeyboardButton('last Online', callback_data='A_F: last_online')
        ],

        [
            InlineKeyboardButton('Gender', callback_data='A_F: Gender'),
            InlineKeyboardButton('Age', callback_data='A_F: Age')
        ],

        [InlineKeyboardButton('Cities', callback_data='A_F: Cities')],

        [InlineKeyboardButton('Done', callback_data='A_F: Search')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="advance searched:",
        reply_markup=reply_markup
    )


async def random_chat(update: Update, context:
ContextTypes.DEFAULT_TYPE):
    """
    Initiates the random chat setup, specifically for gender filtering.
    """
    await interact(update, context)
    if "gender_filter" not in context.user_data:
        context.user_data['gender_filter'] = []
    gender_filter = context.user_data['gender_filter']
    keyboard = [

        [
            InlineKeyboardButton(f"{'✓ ' if 'male' in gender_filter else ''}Male", callback_data="random gender: male"),
            InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}Female",
                                 callback_data="random gender: female"),
        ],
        [
            InlineKeyboardButton('Done', callback_data="random_chat: gender: done"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="random_chat mikhai",
        reply_markup=reply_markup,
    )


async def show_profile_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles requests to show a user's profile based on a '/chaT_<generated_id>' command.
    Validates the generated ID and then calls the profile handler to display the profile.
    """
    user_id = update.effective_user.id
    target_id_parts = update.message.text.split('_', 1)
    if len(target_id_parts) < 2:
        await update.message.reply_text('invalid format. use/chaT_<somthing>')
        return
    command, target_id_generated = target_id_parts
    if not target_id_generated:
        await update.message.reply_text('invalid item. Could not find this item')
        return
    if not user_db.get_user_id_from_generated_id(target_id_generated):
        await update.message.reply_text('This user is not registered!')
        return
    target_id = user_db.get_user_id_from_generated_id(target_id_generated)
    await profile.show_target_profile(update, context, target_id)


# ___________________________________________________________________________________________
#                             Gold Gallery initiator
# ___________________________________________________________________________________________
# todo make real calculate the price send items list
async def gold_dollar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Scrapes gold and dollar prices and sends them to the user.
    Displays live prices from tgju.org and goldpricez.com, and includes a calculator button.
    Handles potential errors during price fetching.
    """
    await interact(update, context)
    user_id = update.effective_chat.id
    checking_msg = await context.bot.send_message(user_id, text='Checking site .... wait')
    try:
        latest_price = gold_db.get_latest_update()
        if not latest_price:
            raise Exception("Could not fetch prices")

        keyboard = [
            [
                InlineKeyboardButton(f'calculator', callback_data=f'{calculator.calculate_command}'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # todo format the rials mostly
        # todo add date hr
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=checking_msg.message_id,
            text=f'Updated @ {latest_price.time_check_ir.strftime('%Y-%m-%d %H:%M')}\n'
                 f'gold 18k 1gr Iran= {latest_price.gold_18k_ir:,} Rial\n'
                 f'dollar Iran = {latest_price.dollar_ir_rial:,} Rial\n'
                 f'gold 18k 1gr international = ${latest_price.gold_18k_international_dollar}\n'
                 f'gold 18k 1gr international into ir = {latest_price.gold_18k_international_rial:,} Rial\n',
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Gold price error: {e}")
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=checking_msg.message_id,
            text="⚠️ Sorry, I couldn't fetch the latest prices right now.\n\n"
                 "Please try again in a few minutes."
        )


# ___________________________________________________________________________________________
#                             Torob initiator
# ___________________________________________________________________________________________
# todo make real calculate the price send items list
async def torob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the Torob price tracking feature.
    Provides options to check existing items or add new ones.
    """
    await interact(update, context)

    keyboard = [
        [
            InlineKeyboardButton(f'Check My Items/edit', callback_data=f'torob: check'),
        ],
        [
            InlineKeyboardButton("Addd New items", callback_data=torob_conversation.query_add_pattern),
        ],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Torob Scraper: ",
        reply_markup=reply_markup
    )


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the '/item_<item_id>' command to enter item editing mode for Torob items.
    Allows users to edit price, URL, name, or delete an item.
    """
    user_id = update.effective_user.id
    item_id_parts = update.message.text.split('_', 1)
    if len(item_id_parts) < 2:
        await update.message.reply_text('invalid format. use/item_<somthing>')
        return
    try:
        command, item_id = item_id_parts
        item_data = torob_db.get_item_by_id(int(item_id))
    except ValueError:
        await update.message.reply_text('invalid format. use/item_<somthing>')
        return
    if not item_data:
        await update.message.reply_text('invalid item. Could not find this item')
        return
    if not torob_db.check_ownership(user_id, int(item_id)):
        await update.message.reply_text('You are now owner of this item / plz insert a valid code')
        return
    context.user_data['editing_item_id'] = int(item_id)
    keyboard = [
        [
            InlineKeyboardButton('Edit Price', callback_data=f'{torob_conversation.edit_price_pattern}'),
            InlineKeyboardButton('Edit URL', callback_data=f'{torob_conversation.edit_url_pattern}'),
            InlineKeyboardButton('Edit Name', callback_data=f'{torob_conversation.edit_name_pattern}')
        ],
        [
            InlineKeyboardButton('delete', callback_data=f'{torob_conversation.delete_item_pattern}')
        ],
        [
            InlineKeyboardButton('home', callback_data='item_edit:home')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id,
                                   text=f"✅ Item On Edit Mode!\n\n"
                                        f"Item: {item_data.name_of_item}\n"
                                        f"Current Highest Price: {item_data.user_preferred_price}\n\n"
                                        f"Current URL: {item_data.torob_url}\n\n"
                                        f"What would you like to edit?",
                                   reply_markup=reply_markup)


# todo add points to users then add price for running scrap or they can w8 for 12pm to get updated

# ___________________________________________________________________________________________
#                             inline keys
# ___________________________________________________________________________________________

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all inline button callbacks.
    Routes to specific functions based on the callback data prefix.
    """
    await interact(update, context)
    query = update.callback_query

    await query.answer()

    if query.data.startswith('A_F:'):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        user_filter = context.user_data['user_filter']
        filter_name = query.data.split(':')[1].strip().lower()
        if filter_name == "dis":
            await distance_filter_handler(query, context)
        if filter_name == 'last_online':
            await last_online_filter_handler(query, context)
        if filter_name == 'gender':
            await gender_filter_handler(query, context)
        if filter_name == 'age':
            await age_filter_handler(query, context)
        if filter_name == 'cities':
            await cities_filter_handler(query, context)
        if filter_name == 'search':
            await search_filters_handler(query, context)


    elif query.data.startswith('A_F_D'):
        await interact(query, context)
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if query.data.startswith('A_F_D: dis_filter:'):
            get_dis_filter(query, context)
        if query.data.startswith("A_F_D: last_online_filter:"):
            get_last_online_filter(query, context)
        if query.data.startswith("A_F_D: gender: done"):
            get_gender_filter(query, context)
        await update_advance_search(query, context)

    # this is get of gender filter
    elif query.data.startswith("gender:"):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "gender_filter" not in context.user_data:
            context.user_data['gender_filter'] = []
        gender_filter = context.user_data['gender_filter']
        action = query.data.split(":")[1].strip().lower()
        if action in ["male", "female"]:
            # Toggle selection
            if action in gender_filter:
                gender_filter.remove(action)
            else:
                gender_filter.append(action)

            # Update the message with new buttons
            await gender_filter_handler(query, context)
    elif query.data.startswith("random gender:"):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "gender_filter" not in context.user_data:
            context.user_data['gender_filter'] = []
        gender_filter = context.user_data['gender_filter']
        action = query.data.split(":")[1].strip().lower()
        if action in ["male", "female"]:
            # Toggle selection
            if action in gender_filter:
                gender_filter.remove(action)
            else:
                gender_filter.append(action)

            # Update the message with new buttons
            await random_chat_gender_done(query, context)
    elif query.data.startswith("random_chat: gender: done"):
        await user_message.handle_random_chat(update, context)
    elif query.data.startswith(user_message.button_start_with_command):
        await interact(update, context)

        await user_message.buttons_set(update, context)

    # this is get of age filter
    elif query.data.startswith("age_filter:"):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "age_filter" not in context.user_data['user_filter']:
            context.user_data['user_filter']['age_filter'] = []
        age_filter = context.user_data['user_filter']['age_filter']
        # using call back to get filter
        action = int(query.data.split(':')[1].strip())
        if action in age_filter:
            age_filter.remove(action)
        else:
            age_filter.append(action)
        await age_filter_handler(query, context)

    # this is get of city filter
    elif query.data.startswith("city_filter:"):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "city_filter" not in context.user_data['user_filter']:
            context.user_data['city_filter'] = []
        city_filter = context.user_data['user_filter']['city_filter']
        action = query.data.split(":")[1].strip().lower()
        # Toggle selection
        if action == "all":
            if len(city_filter) == len(iran_cities_fa):
                city_filter.clear()
            else:
                city_filter.clear()
                for city in iran_cities_fa:
                    city_filter.append(city)
        elif action in city_filter:
            city_filter.remove(action)
        else:
            city_filter.append(action)
        # Update the message with new buttons
        await cities_filter_handler(query, context)

    elif query.data.startswith('torob:'):
        action = query.data.split(':')[1].strip().lower()
        if action == "check":
            await check_torob_list(query, context)
        if action == 'new':
            pass
        if action == 'update':
            pass

    elif query.data.startswith('item_edit:'):
        action = query.data.split(':')[1].strip().lower()
        if action == 'price':
            pass
        if action == 'url':
            pass
        if action == 'name':
            pass
        if action == 'delete':
            pass
        if action == 'home':
            pass

    elif query.data == f'{calculator.calculate_command}':

        await query.answer()

        # Get the conversation handler
        conv_handler = calculator.get_calculated_price_conversation_handler()

        # Start the conversation manually
        await conv_handler.trigger(update, context)

        await query.delete_message()

    elif query.data == 'page_before':
        # Decrement current_page by 1 to go to the previous page
        await search_filters_handler(query, context, current_page=context.user_data.get('current_page', 1) - 1)

    elif query.data == 'page_next':
        # Increment current_page by 1 to go to the next page
        await search_filters_handler(query, context, current_page=context.user_data.get('current_page', 1) + 1)

    await profile.buttons(update, context)


# _______________________________________________________________________________
# __________________Query functions for inline buttons___________________________
# _______________________________________________________________________________


# __________________Chat filter for user_data['user_filter']_____________________
async def distance_filter_handler(query, context):
    """
    Displays inline keyboard for distance filtering options in advanced search.
    """
    keyboard = [
        [
            InlineKeyboardButton('5km', callback_data='A_F_D: dis_filter: 5km'),
            InlineKeyboardButton('10km', callback_data='A_F_D: dis_filter: 10km'),
        ],
        [
            InlineKeyboardButton('15km', callback_data='A_F_D: dis_filter: 15km'),
            InlineKeyboardButton('20km', callback_data='A_F_D: dis_filter: 20km'),
        ],
        [
            InlineKeyboardButton('25km', callback_data='A_F_D: dis_filter: 25km'),
            InlineKeyboardButton('30km', callback_data='A_F_D: dis_filter: 30km'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        'Chose',
        reply_markup=reply_markup
    )


def get_dis_filter(query, context):
    """
    Extracts the selected distance filter from the callback query and stores it in user_data.
    """
    dis_filter = query.data.split(':')[2].strip().lower().split('km')[0]
    context.user_data['user_filter']['dis_filter'] = int(dis_filter)


async def last_online_filter_handler(query, context):
    """
    Displays inline keyboard for 'last online' filtering options in advanced search.
    """
    keyboard = [
        [
            InlineKeyboardButton('15min', callback_data='A_F_D: last_online_filter: 15min'),
            InlineKeyboardButton('30min', callback_data='A_F_D: last_online_filter: 30min'),
        ],
        [
            InlineKeyboardButton('1hr', callback_data='A_F_D: last_online_filter: 1hr'),
            InlineKeyboardButton('3hr', callback_data='A_F_D: last_online_filter: 3hr'),
        ],
        [
            InlineKeyboardButton('1day', callback_data='A_F_D: last_online_filter: 1day'),
            InlineKeyboardButton('1week', callback_data='A_F_D: last_online_filter: 1week'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        'Chose',
        reply_markup=reply_markup
    )


def get_last_online_filter(query, context):
    """
    Extracts the selected 'last online' filter from the callback query and stores it in user_data.
    Converts time strings (e.g., '15min') to minutes.
    """
    global dict_last_online
    dict_last_online = {
        "15min": 15,
        "30min": 30,
        "1hr": 60,
        "3hr": 180,
        "1day": 1440,
        "1week": 1080,
    }
    last_online_filter_full = query.data.split(':')[2].strip().lower()
    last_online_filter = dict_last_online[last_online_filter_full]
    context.user_data['user_filter']['last_online_filter'] = last_online_filter


async def gender_filter_handler(query, context):
    """
    Displays inline keyboard for gender filtering in advanced search, with current selections marked.
    Toggles selection of 'male' or 'female'.
    """
    if "gender_filter" not in context.user_data:
        context.user_data['gender_filter'] = []
    gender_filter = context.user_data['gender_filter']
    keyboard = [

        [
            InlineKeyboardButton(f"{'✓ ' if 'male' in gender_filter else ''}Male", callback_data="gender: male"),
            InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}Female", callback_data="gender: female"),
        ],
        [
            InlineKeyboardButton('Done', callback_data="A_F_D: gender: done"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Chose gender:",
        reply_markup=reply_markup,
    )


async def random_chat_gender_done(query, context):
    """
    Updates the gender filter options for random chat, similar to the general gender filter handler.
    """
    if "gender_filter" not in context.user_data:
        context.user_data['gender_filter'] = []
    gender_filter = context.user_data['gender_filter']
    keyboard = [

        [
            InlineKeyboardButton(f"{'✓ ' if 'male' in gender_filter else ''}Male", callback_data="random gender: male"),
            InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}Female",
                                 callback_data="random gender: female"),
        ],
        [
            InlineKeyboardButton('Done', callback_data="random_chat: gender: done"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Chose gender:",
        reply_markup=reply_markup,
    )


# made it two part to put in dict but can be like other in one part to get the way
def get_gender_filter(query, context):
    """
    Stores the selected gender filter into the 'user_filter' dictionary within user_data.
    """
    context.user_data['user_filter']['gender_filter'] = context.user_data['gender_filter']


async def age_filter_handler(query, context, i=None):
    """
    Displays inline keyboard for age filtering in advanced search.
    Allows selection of one or two age values to define a range.
    Handles dynamic display of selected ages.
    """
    if "user_filter" not in context.user_data:
        context.user_data['user_filter'] = {}
    if "age_filter" not in context.user_data['user_filter']:
        context.user_data['user_filter']['age_filter'] = []
    if len(context.user_data['user_filter']['age_filter']) > 2:
        context.user_data['user_filter']['age_filter'].sort()
        a = context.user_data['user_filter']['age_filter'][0]
        b = context.user_data['user_filter']['age_filter'][-1]
        context.user_data['user_filter']['age_filter'].clear()
        context.user_data['user_filter']['age_filter'] = [a, b]
    age_filter = context.user_data['user_filter']['age_filter']
    # --------------->here
    if len(age_filter) == 2:
        keyboard = [
                       [
                           InlineKeyboardButton(
                               f'{'✓ ' if (8 * i + n) + 1 in range(age_filter[0], age_filter[1] + 1) else ''}{(8 * i + n) + 1}',
                               callback_data=f'age_filter: {(8 * i + n) + 1}') for n in range(8)
                       ] for i in range(1, 13)
                   ] + [
                       [
                           InlineKeyboardButton('Done', callback_data="A_F_D: age: done"),
                       ],
                   ]
    else:
        keyboard = [
                       [
                           InlineKeyboardButton(f'{'✓ ' if (8 * i + n) + 1 in age_filter else ''}{(8 * i + n) + 1}',
                                                callback_data=f'age_filter: {(8 * i + n) + 1}') for n in range(8)
                       ] for i in range(1, 13)
                   ] + [
                       [
                           InlineKeyboardButton('Done', callback_data="A_F_D: age: done"),
                       ],
                   ]
    if len(context.user_data['user_filter']['age_filter']) == 2:
        context.user_data['user_filter']['age_filter'].sort()
        text = f'from: {context.user_data['user_filter']['age_filter'][0]} to: {context.user_data['user_filter']['age_filter'][1]}'
    elif len(context.user_data['user_filter']['age_filter']) == 1:
        text = f'-{context.user_data['user_filter']["age_filter"][0]}-'
    else:
        text = "plz chose starting age:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise  # Re-raise if it's a different error
    # get of this part is in buttons functions


async def cities_filter_handler(query, context):
    """
    Displays inline keyboard for city filtering in advanced search, with current selections marked.
    Allows toggling individual cities or selecting/deselecting all cities.
    """
    if "city_filter" not in context.user_data['user_filter']:
        context.user_data['user_filter']['city_filter'] = []
    city_filter = context.user_data['user_filter']['city_filter']
    keyboard = [
                   [
                       InlineKeyboardButton(f'{'✓ ' if city in city_filter else ""}{city}',
                                            callback_data=f'city_filter: {city}') for city
                       in iran_cities_fa[i * 4: (i * 4) + 4]
                   ] for i in range(10)

               ] + [
                   [
                       InlineKeyboardButton('ALL', callback_data="city_filter: all"),
                       InlineKeyboardButton('Done', callback_data="A_F_D: city: done"),
                   ],
               ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        'Chose',
        reply_markup=reply_markup
    )


# todo check if this even needed can be used for clear eh
async def search_filters_handler(query, context, current_page=1):
    """
        Handles user search requests by applying filters and displaying matching profiles.

        Processes user search criteria from context, queries the database for matches,
        and formats the results into a paginated message with profile previews.

        Features:
        - Online status detection ('Online' or time-based last seen)
        - Distance display in kilometers
        - Profile linking via /chaT_[id] commands
        - Automatic filter reset after search

        Args:
            query: Telegram callback query object
            context: Context object containing user data and filters
            current_page: shows the number of page it shows starts from one default

        Returns:
            None (edits the original message with results)

        Side Effects:
            - Updates user data if no generated_id exists
            - Resets user_filter in context after search
            - Modifies the original query message
        """
    user_id = query.from_user.id
    generated_id = context.user_data.get('generated_id')
    if not generated_id:
        user_db.add_or_update_user(user_id, context.user_data)

    await interact(query, context)
    selected_users = user_db.get_filtered_users(context.user_data)
    # reseting filter
    context.user_data['user_filter'] = {}
    # todo return a list of n ppl with keys to C profile or chat
    all_pages = []
    page = ''
    num_show_page = 10
    # Store current page in user_data to persist across callbacks
    context.user_data['current_page'] = current_page

    # Calculate start and end indices for pagination
    start_index = (current_page - 1) * num_show_page
    end_index = start_index + num_show_page

    paginated_users = selected_users[start_index:end_index]

    if not paginated_users and selected_users:
        # If no users on this page but there are other pages, go to first page
        context.user_data['current_page'] = 1
        start_index = 0
        end_index = num_show_page
        paginated_users = selected_users[start_index:end_index]

    for data in paginated_users:
        name = data['user'].name
        generated_id = data['user'].generated_id
        distance = int(data['distance'])
        if data['is_online']:
            last_online = 'Online'
        else:
            if int(data["mins_ago"]) <= 60:
                last_online = f'{int(data["mins_ago"])} mins ago'
            elif int(data["mins_ago"]) <= 1440:
                last_online = f'{int(int(data["mins_ago"]) / 60)} hr ago'
            elif int(data["mins_ago"]) <= 10080:
                last_online = f'{int(int(data["mins_ago"]) / 1440)} day ago'
            else:
                last_online = "long time ago"

        gender = data['user'].gender.lower()
        city = data['user'].city
        age = data['user'].age
        user_id = data['user'].user_id

        # check persian rtl and ltr fucking it
        # todo need a link to see other ppl profiles show profile for others
        # todo need to find how connect two ppl in robot
        # todo need to keshoii model mostlykly it was with robot name inline shit
        # todo make a home button to go back start
        # todo handle wrong type and wrong commends
        # todo handle random chat

        # todo important change data base to give any user an maked id to not use real user id
        note = f'\nName:{"👨🏻‍🦱" if gender == 'male' else '👩🏻'} {name}\nAge: {age} Years old\nLast Online: {last_online}\ncity: {city}\nDistance: {distance}km away\n\nuser_id: /chaT_{generated_id}\n\n{divider}\n'
        page += note
    all_pages.append(page)

    total_pages = math.ceil(len(selected_users) / num_show_page)

    keyboard_buttons = []
    if total_pages > 1:
        if current_page > 1:
            keyboard_buttons.append(InlineKeyboardButton('Back', callback_data='page_before'))
        if current_page < total_pages:
            keyboard_buttons.append(InlineKeyboardButton('Next', callback_data='page_next'))

    reply_markup = InlineKeyboardMarkup([keyboard_buttons]) if keyboard_buttons else None

    if paginated_users:  # Use paginated_users to check if there are results for the current page
        await query.edit_message_text(
            text=page,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            text='Could not find any profile for this filter\n\n/start'
        )


# todo update each button to has the filter applied
async def update_advance_search(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Updates the displayed advanced search message with the currently applied filters.
    Reflects selections for distance, last online, gender, age, and cities on the buttons.
    """
    filter_data = context.user_data['user_filter']
    if "dis_filter" in filter_data:
        dis = f": {filter_data['dis_filter']}km"
    else:
        dis = ""

    if "last_online_filter" in filter_data:
        reverse_dict = {v: k for k, v in dict_last_online.items()}
        last_online = f"{reverse_dict[filter_data['last_online_filter']]}"
    else:
        last_online = ""

    if "gender_filter" in filter_data:
        gender = ""
        for g in filter_data["gender_filter"]:
            gender = f'{gender}{g}, '
    else:
        gender = ""

    if "age_filter" in filter_data:
        if len(filter_data['age_filter']) == 1:
            age = f": {filter_data['age_filter'][0]}"
        elif len(filter_data['age_filter']) == 2:
            age = f": {filter_data['age_filter'][0]} to {filter_data['age_filter'][1]}"
        else:
            age = []
    else:
        age = ""

    if "city_filter" in filter_data:
        num_cities = f": {len(filter_data['city_filter'])}"
    else:
        num_cities = ""

    keyboard = [
        [
            InlineKeyboardButton(f"Distance{dis}", callback_data='A_F: Dis'),
            InlineKeyboardButton(f'last Online {last_online}', callback_data='A_F: last_online')
        ],

        [
            InlineKeyboardButton(f'{gender if gender else "Gender"}', callback_data='A_F: Gender'),
            InlineKeyboardButton(f'Age{age}', callback_data='A_F: Age')
        ],

        [InlineKeyboardButton(f'Cities{num_cities}', callback_data='A_F: Cities')],

        [InlineKeyboardButton('Search', callback_data='A_F: Search')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="advance searched:",
        reply_markup=reply_markup
    )


# todo check if this even needed i think it is a function to create more button for items of gold gallery we have
async def calculator_gold(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Placeholder for a gold calculator function.
    """
    pass


# todo add button to calculate item for this we need to give  each user point after creating profile and reduce it when they use this
# todo update db with point
# todo update profile to give point after creation
async def check_torob_list(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays a list of Torob items tracked by the user, including their latest prices and check times.
    Provides options to add new items or edit existing ones.
    """
    user_id = query.from_user.id
    user_items = torob_db.get_user_items(user_id)
    final_note = ""
    keyboard = [
        [InlineKeyboardButton('Add Item', callback_data=torob_conversation.query_add_pattern)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if user_items:
        for item in user_items:
            name = item.name_of_item
            latest_price = torob_db.get_latest_price(item.item_id)
            signal_price = '✅' if latest_price and latest_price <= item.user_preferred_price else '❌'
            latest_check = torob_db.get_latest_check(item.item_id)
            item_id = item.item_id
            if latest_check:
                latest_check_format = latest_check.strftime("%Y/%m/%d: %H")
            if latest_check and latest_price:
                item_note = f"{signal_price}{name} @{latest_check}: with price of {latest_price}\n\nedit /item_{item_id}\n\n{divider}"
                final_note += item_note
            else:
                item_note = f"\n{signal_price}{name} is not yet Checked plz wait\n\nedit /item_{item_id}\n\n{divider}\n"
                final_note += item_note
    if final_note:
        await query.edit_message_text(
            text=final_note,
            reply_markup=reply_markup

        )
    else:
        await query.edit_message_text(
            text="there is noting to show plz add some \n\n /start",
            reply_markup=reply_markup
        )


# _______________________________________________________________________________
# ________________________Robot run and handlers_________________________________
# _______________________________________________________________________________

if __name__ == "__main__":
    # Initialize the Telegram Application Builder with bot token and concurrent updates.
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).concurrent_updates(True).build()
    # todo currect the way of messagehandler to not intract with them in casual chat

    # Create Handlers for various commands and message types.
    start_handler = CommandHandler("start", start)
    chat_handler = MessageHandler(filters.Regex(r"^ChaT$"), chat)
    advance_search_handler = MessageHandler(filters.Regex(r"^Advance Search"), advance_search)
    random_chat_handler = MessageHandler(filters.Regex(r"^Random chat$"), random_chat)
    gold_dollar_handler = MessageHandler(filters.Regex(r"^Gold & Dollar$"), gold_dollar)
    torob_handler = MessageHandler(filters.Regex(r"^Torob price check$"), torob)
    torob_edit_handler = MessageHandler(filters.Regex(r'^/item_'), edit_command)
    show_profile_handler = MessageHandler(filters.Regex(r'^/chaT_'), show_profile_request)
    my_profile = CommandHandler("profile", profile.show_my_profile)
    # Inline button handler
    buttons_handler = CallbackQueryHandler(buttons)

    # Add handlers to the application.
    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    application.add_handler(advance_search_handler)
    application.add_handler(random_chat_handler)
    application.add_handler(show_profile_handler)
    application.add_handler(gold_dollar_handler)
    application.add_handler(torob_handler)
    application.add_handler(torob_edit_handler)
    # These conversations have their handlers defined within their respective classes (e.g., telegram_conversation.py)
    application.add_handler(calculator.get_calculated_price_conversation_handler())

    application.add_handlers(profile.get_all_handlers())
    application.add_handlers(torob_conversation.get_all_handlers())

    application.add_handler(my_profile)
    application.add_handlers(user_message.message_handlers())

    # Add the generic inline button handler.
    application.add_handler(buttons_handler)

    # Run the bot, starting the polling for updates.
    application.run_polling()

# _______________________________________________________________________________
# ___________________________Problems & checks___________________________________
# _______________________________________________________________________________

# todo conversation gold kar nemikard check she