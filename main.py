import logging
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
from telegram_chat_handler import AnonymousChat, AnonymousMessage
import json
import os
from datetime import datetime , timedelta


divider = '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️'
#todo add a handler at top for each interaction with bot get trigger to make user data and user session and etc..
#todo handle some errors in advance chat likebeing emty in profiles
#todo For the filter handling in main.py, you could create a FilterHandler class:
os.makedirs("profiles", exist_ok=True)

# Ensure directory exists
os.makedirs("profiles", exist_ok=True)

anonymous_chat=AnonymousChat()
anonymous_msg = AnonymousMessage()

#todo put a place for all commands and queries
anonymous_chat.start_command = 'anom_chat'
anonymous_msg.start_command = 'anom_message'

anonymous_chat.leave_command = 'leave_anom_chat'
anonymous_msg.leave_command = 'leave_anom_message'
#todo each act in robot update user last online
#___________________conversations_________________________________
profile = Profile()
calculator = Calculator()
torob_conversation = TorobConversation()
#___________________data_bases_________________________________
#todo make it one db with two table (already is xD)
#todo make a postoger db engine
gold_db = GoldPriceDatabase()
user_db = UserDatabase()
chat_db = ChatDatabase()
torob_db = TorobDb()


#todo make a tab to check divar or digikala or shapoor (web scraping)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#___________________________________________________________________________________________
#                             Robot initiator
#___________________________________________________________________________________________
def interact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        This handler activates for almost any user interaction.
        It ensures the user's session exists and updates their last_online status.
        """
    user_id = update.effective_user.id
    chat_db.create_user_session(user_id)

    context.user_data['last_online'] = datetime.now
    user_db.add_or_update_user(user_id, context.user_data)

#todo need to be start over after parts maybe change handler to be not only command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interact(update, context)
    user_db.get_user_data(update.effective_user.id, context.user_data)
    if context.user_data['name']:
        keyboard= [
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
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'start',
        reply_markup=reply_markup
    )

#___________________________________________________________________________________________
#                             Chat initiator
#___________________________________________________________________________________________

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interact(update, context)
    keyboard = [
        [KeyboardButton("Random chat")],
        [
            KeyboardButton(f'/{anonymous_chat.start_command}'),
            KeyboardButton(f'/{anonymous_msg.start_command}')
        ],
        [KeyboardButton('Advance Search')]
    ]

    reply_markup=ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='What you looking for?',
        reply_markup=reply_markup,
    )

#todo almost done
async def advance_search(update: Update, context:
ContextTypes.DEFAULT_TYPE):
    interact(update, context)
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
        text= "advance searched:",
        reply_markup=reply_markup
    )
#todo need to work on
async def random_chat(update: Update, context:
ContextTypes.DEFAULT_TYPE):
    interact(update, context)
    if "gender_filter" not in context.user_data:
        context.user_data['gender_filter']=[]
    gender_filter = context.user_data['gender_filter']
    keyboard = [

        [
            InlineKeyboardButton( f"{'✓ ' if 'male' in gender_filter else ''}Male", callback_data="gender: male"),
            InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}Female", callback_data="gender: female"),
        ],
        [
            InlineKeyboardButton('Done', callback_data="random_chat: done"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="random_chat mikahi",
        reply_markup=reply_markup,
    )


#___________________________________________________________________________________________
#                             Gold Gallery initiator
#___________________________________________________________________________________________
#todo make real calculate the price send items list
async def gold_dollar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interact(update, context)

    latest_price = gold_db.get_latest_update()

    keyboard = [
        [
        InlineKeyboardButton(f'calculator', callback_data=f'{calculator.calculate_command}'),
        InlineKeyboardButton("done", callback_data="home")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)


    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text= f'gold 18k 1gr Iran= {latest_price.gold_18k_ir} Rial\n'
              f'dollar Iran = {latest_price.dollar_ir_rial} Rial\n'
              f'gold 18k 1gr international = ${latest_price.gold_18k_international_dollar}\n'
              f'gold 18k 1gr international into ir = {latest_price.gold_18k_international_rial} Rial\n',
        reply_markup=reply_markup
    )
#___________________________________________________________________________________________
#                             Torob initiator
#___________________________________________________________________________________________
#todo make real calculate the price send items list
async def torob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interact(update, context)


    keyboard = [
        [
        InlineKeyboardButton(f'Check My Items', callback_data=f'torob: check'),
        ],
        [
        InlineKeyboardButton("Addd New items", callback_data=torob_conversation.query_add_pattern),
        InlineKeyboardButton("Update My Items", callback_data="torob: update"),
        ],
        [
        InlineKeyboardButton(f'Home', callback_data=f'start'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)


    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text= "Torob Scraper: ",
        reply_markup=reply_markup
    )

#___________________________________________________________________________________________
#                             inline keys
#___________________________________________________________________________________________

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    interact(update, context)
    query = update.callback_query

    await query.answer()


    if query.data.startswith('A_F:'):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter']= {}
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
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter']= {}
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
            context.user_data['user_filter']= {}
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


    #this is get of age filter
    elif query.data.startswith("age_filter:"):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter']= {}
        if "age_filter" not in context.user_data['user_filter']:
            context.user_data['user_filter']['age_filter'] = []
        age_filter = context.user_data['user_filter']['age_filter']
        #using call back to get filter
        action = int(query.data.split(':')[1].strip())
        if action in age_filter:
            age_filter.remove(action)
        else:
            age_filter.append(action)
        await age_filter_handler(query, context)

    # this is get of city filter
    elif query.data.startswith("city_filter:"):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter']= {}
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


    elif query.data == f'{calculator.calculate_command}':

        await query.answer()

        # Get the conversation handler

        conv_handler = calculator.get_calculated_price_conversation_handler()

        # Start the conversation manually

        await conv_handler.trigger(update, context)

        await query.delete_message()


    elif query.data == "home":
        await start(update, context)


#_______________________________________________________________________________
#__________________Query functions for inline buttons___________________________
#_______________________________________________________________________________


#__________________Chat filter for user_data['user_filter']_____________________
async def distance_filter_handler(query, context):

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
    dis_filter = query.data.split(':')[2].strip().lower().split('km')[0]
    context.user_data['user_filter']['dis_filter'] = int(dis_filter)


async def last_online_filter_handler(query, context):
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
    if "gender_filter" not in context.user_data:
        context.user_data['gender_filter']=[]
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

#made it two part to put in dict but can be like other in one part to get the way
def get_gender_filter(query, context):
    context.user_data['user_filter']['gender_filter'] = context.user_data['gender_filter']


async def age_filter_handler(query, context, i=None):

    if "user_filter" not in context.user_data:
        context.user_data['user_filter'] = {}
    if "age_filter" not in context.user_data['user_filter']:
        context.user_data['user_filter']['age_filter']=[]
    if len(context.user_data['user_filter']['age_filter']) > 2:
        context.user_data['user_filter']['age_filter'].sort()
        a= context.user_data['user_filter']['age_filter'][0]
        b= context.user_data['user_filter']['age_filter'][-1]
        context.user_data['user_filter']['age_filter'].clear()
        context.user_data['user_filter']['age_filter']= [a,b]
    age_filter = context.user_data['user_filter']['age_filter']
    #--------------->here
    if len(age_filter) == 2:
        keyboard = [
                       [
                           InlineKeyboardButton(
                               f'{'✓ ' if (8 * i + n) + 1 in range(age_filter[0], age_filter[1]+1) else ''}{(8 * i + n) + 1}',
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
                    InlineKeyboardButton(f'{'✓ ' if (8*i + n)+1 in age_filter else ''}{(8*i + n)+1}',
                                         callback_data=f'age_filter: {(8*i + n)+1}') for n in range(8)
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
    #get of this part is in buttons functions


async def cities_filter_handler(query, context):
    if "city_filter" not in context.user_data['user_filter']:
        context.user_data['user_filter']['city_filter']=[]
    city_filter = context.user_data['user_filter']['city_filter']
    keyboard = [
                   [
                       InlineKeyboardButton(f'{'✓ ' if city in city_filter else ""}{city}',
                                            callback_data=f'city_filter: {city}') for city
                       in iran_cities_fa[i*4 : (i*4)+4]
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

#todo check if this even needed can be used for clear eh
async def search_filters_handler(query, context):
    selected_users = user_db.get_filtered_users(context.user_data)
    #reseting filter
    context.user_data['user_filter'] = {}
    #todo return a list of n ppl with keys to C profile or chat
    first_page = ''
    for data in selected_users[:10]:
        big_line = '_________________________________'
        name = data['user'].name
        distance = int(data['distance'])
        if data['is_online']:
            last_online = 'Online'
        else:
            if int(data["mins_ago"]) <= 60:
                last_online = f'{int(data["mins_ago"])} mins ago'
            elif int(data["mins_ago"]) <= 1440:
                last_online = f'{int(int(data["mins_ago"]) / 60)} hr ago'
            elif int(data["mins_ago"]) <= 10080:
                last_online = f'{int(int(data["mins_ago"])/ 1440)} day ago'
            else:
                last_online = "long time ago"

        gender = data['user'].gender.lower
        city = data['user'].city
        age = data['user'].age
        #check persian rtl and ltr fucking it
        #todo need a link to see other ppl profiles show profile for others
        #todo need to find how connect two ppl in robot
        #todo need to keshoii model mostlykly it was with robot name inline shit
        #todo make a home button to go back start
        #todo handle wrong type and wrong commends
        #todo handle random chat


        note = f'\n{name}\n{age} Years old\n{last_online}\ncity: {city}\n{distance}km away\n{big_line}\n'
        first_page = first_page + note
    #todo can go next page on that list
    #todo get filter in first go top and make a filter dictionary or somthing like that

    await query.edit_message_text(
        text=first_page
    )

#todo update each button to has the filter applied
async def update_advance_search(query, context: ContextTypes.DEFAULT_TYPE):
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
        text= "advance searched:",
        reply_markup=reply_markup
    )


#todo check if this even needed i think it is a function to create more button for items of gold gallery we have
async def calculator_gold(query, context: ContextTypes.DEFAULT_TYPE):
    pass

async def check_torob_list(query, context:ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    user_items = torob_db.get_user_items(user_id)
    final_note = ""
    if user_items:
        for item in user_items:
            name = item.name_of_item
            latest_price = torob_db.get_latest_price(item.item_id)
            signal_price = '✅' if latest_price <= item.user_preferred_price else '❌'
            latest_check =  torob_db.get_latest_check(item.item_id)
            if latest_check:
                latest_check_format = latest_check.strftime("%Y/%m/%d: %H")
            item_note = f"{signal_price}{name} @{latest_check}: with price of {latest_price}\n{divider}\n"
            final_note += item_note
    await query.edit_message_text(
        text=final_note,

    )

#_______________________________________________________________________________
#________________________Robot run and handlers_________________________________
#_______________________________________________________________________________

if __name__ == "__main__":
    application = ApplicationBuilder().token("7651582199:AAHj9Ib_NOXga_iOZiQ5G9dD4pfC5AuFr0U").concurrent_updates(True).build()
    #todo currect the way of messagehandler to not intract with them in casual chat
    #create handler
    start_handler = CommandHandler("start", start)
    chat_handler = MessageHandler(filters.Regex(r"^ChaT$"), chat)
    advance_search_handler = MessageHandler(filters.Regex(r"^Advance Search"), advance_search)
    random_chat_handler = MessageHandler(filters.Regex(r"^Random chat$"), random_chat)
    gold_dollar_handler = MessageHandler(filters.Regex(r"^Gold & Dollar$"), gold_dollar)
    torob_handler = MessageHandler(filters.Regex(r"^Torob price check$"), torob)
    my_profile = CommandHandler("profile", profile.show_profile)
        #button
    buttons_handler = CallbackQueryHandler(buttons)


    #add handler
    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    application.add_handler(advance_search_handler)
    application.add_handler(random_chat_handler)
    application.add_handler(gold_dollar_handler)
    application.add_handler(torob_handler)
    #those conversations have handler inside them check the telegram_conversation file
    application.add_handler(profile.get_profile_create_conversation_handler())
    application.add_handler(calculator.get_calculated_price_conversation_handler())
    application.add_handler(torob_conversation.torob_add_handler())

    application.add_handler(my_profile)
    application.add_handlers(anonymous_chat.anonymously_chat_handlers())
    application.add_handlers(anonymous_msg.anonymously_msg_handlers())

        #buttons
    application.add_handler(buttons_handler)



    application.run_polling()

#_______________________________________________________________________________
#___________________________Problems & checks___________________________________
#_______________________________________________________________________________

#todo conversation gold kar nemikard check she