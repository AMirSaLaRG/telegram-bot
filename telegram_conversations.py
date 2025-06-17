from datetime import datetime, timedelta
import logging
from datetime import timedelta

from pyexpat.errors import messages
from telegram import (Update, InlineQueryResultArticle,
                      InputTextMessageContent, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, ReplyKeyboardRemove,)
from telegram.ext import (InlineQueryHandler, filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler,
                          ConversationHandler)
from data_base import UserDatabase, TorobDb, ChatDatabase
from urllib.parse import urlparse
from telegram_chat_handler import UserMessage

# Initialize DB
user_db = UserDatabase()



# todo last online time
# todo  in self profile add buttons (who liked, see friends, edit(each step a button), torob items, add shop:new, etc, ..)
class Profile:
    def __init__(self):
        self.PHOTO, self.NAME, self.AGE, self.GENDER, self.ABOUT, self.LOCATION = range(6)
        self.create_commend = 'createprofile'
        self.button_starter_command = 'start_profile_buttons:'
        self.DIRECT_TEXT = 1
        self.msg_request_pattern = 'user_wants_to_send_direct_msg'
        self.msg_req_command = 'the_msg_req_ask'
        self.my_profile_key_starter = 'my_Profile_command_starter'


    def get_profile_create_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler(self.create_commend, self.start_profile)],
            states={
                self.PHOTO: [MessageHandler(filters.PHOTO, self.handle_photo)],
                self.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name)],
                self.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_age)],
                self.GENDER: [MessageHandler(filters.Regex("^(Male|Female|Other)$"), self.handle_gender)],
                self.ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_about)],
                self.LOCATION: [MessageHandler(filters.LOCATION, self.handle_location)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    def direct_msg_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_msg_request, pattern=f'^{self.msg_request_pattern}')],
            states={
                self.DIRECT_TEXT : [MessageHandler(filters.TEXT, self.handle_direct_msg)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]

        )


    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Profile creation cancelled')
        return ConversationHandler.END

    async def start_profile(self, update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['user_id'] = update.effective_user.id
        await update.message.reply_text(
            "Lets create your profile.\n First send me your photo",
            reply_markup=ReplyKeyboardRemove()
        )
        return self.PHOTO

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # check photo
        if not update.message.photo:
            await update.message.reply_text("plz send your photo!")
            return self.PHOTO

        # store highest resolution
        photo_file = await update.message.photo[-1].get_file()
        context.user_data['profile_photo'] = photo_file.file_id

        await update.message.reply_text("Great!! \n now send me your name")
        return self.NAME

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['name'] = update.message.text

        await update.message.reply_text("What's your age?")
        return self.AGE

    async def handle_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            age = int(update.message.text)
            if age < 13 or age > 120:
                await update.message.reply_text(
                    "⚠️ Please enter a valid age between 13-120."
                    "\n\nHow old are you?"
                )
                return self.AGE
            context.user_data['age'] = age
        except ValueError:
            await update.message.reply_text(
                "❌ That doesn't look like a valid age."
                "\n\nPlease enter your age as a number (e.g. 25):"
            )
            return self.AGE

        # Create gender selection keyboard
        reply_keyboard = [["Male"], ["Female"], ["Other"]]
        await update.message.reply_text(
            "Select your gender:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder="Your gender?"
            )
        )
        return self.GENDER

    async def handle_gender(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['gender'] = update.message.text

        await update.message.reply_text(
            "Tell me something about yourself (max 200 characters):",
            reply_markup=ReplyKeyboardRemove()
        )
        return self.ABOUT

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(update.message.text) > 200:
            await update.message.reply_text("Please keep it under 200 characters!")
            return self.ABOUT

        context.user_data['about'] = update.message.text

        # Request location with a button
        reply_keyboard = [[KeyboardButton("Share Location", request_location=True)]]
        await update.message.reply_text(
            "Finally, share your location:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True,
            )
        )
        return self.LOCATION

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        location = update.message.location
        context.user_data['location'] = (location.latitude, location.longitude)
        context.user_data['latitude'] = context.user_data['location'][0]
        context.user_data['longitude'] = context.user_data['location'][1]


        # Save the complete profile
        # self.save_profile(update.effective_user.id, context.user_data)
        user_db.add_or_update_user(update.effective_user.id ,context.user_data)

        # Display the profile
        await self.show_my_profile(update, context)

        return ConversationHandler.END

    async def show_my_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.load_profile(update, context)
        user_id = update.effective_user.id

        profile = user_db.get_user_information(user_id)
        time_dif = datetime.now() - profile.last_online
        if time_dif <= timedelta(minutes=5):
            last_online = 'Online'
        elif time_dif < timedelta(hours=1):
            last_online = f'{round(time_dif.seconds / 60)}min ago'
        elif time_dif <= timedelta(hours=24):
            last_online = f'{round(time_dif.seconds / 3600)}hr ago'
        else:
            last_online = f'{time_dif.days} days ago'
        text = (
            f"\n\n\n\n🏷 Name: {profile.name if profile.name else "Not sat yet"}\n"
            f"🔢 Age: {profile.age if profile.age else "Not sat yet"}\n"
            f"👤 Gender: {profile.gender if profile.gender else "Not sat yet"}\n"
            f"📝 About: {profile.about if profile.about else "Not sat yet"}\n"
            f"🕰 online: {last_online if profile.last_online else '"Long time ago"'}"
            f"\n\nuser_id: /chaT_{profile.generated_id}"
            "\n\n\n"

        )

        keyboard = [
            [
                InlineKeyboardButton('Edit', callback_data=f'{self.my_profile_key_starter}: edit'),
                InlineKeyboardButton('Update Location', callback_data=f'{self.my_profile_key_starter}: update location')
            ],
            [
                InlineKeyboardButton('Who liked', callback_data=f'{self.my_profile_key_starter}: liked'),
                InlineKeyboardButton('Friends', callback_data=f"{self.my_profile_key_starter}: friends")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        if profile.profile_photo:
            await update.message.reply_photo(
                photo=profile.profile_photo,
                caption=text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(text)

    async def show_my_profile_edit_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.load_profile(update, context)
        keyboard = [
            [
                InlineKeyboardButton('Edit Name', callback_data='edit'),
                InlineKeyboardButton('Edit About', callback_data='update location')
            ],
            [
                InlineKeyboardButton('Edit City', callback_data='liked'),
                InlineKeyboardButton('Edit Photo', callback_data="friends")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query
        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )



    async def show_target_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id):
        self.load_profile(update, context)

        profile = user_db.get_user_information(target_id)
        time_dif = datetime.now() - profile.last_online
        if time_dif <= timedelta(minutes=5):
            last_online = 'Online'
        elif time_dif < timedelta(hours=1):
            last_online = f'{round(time_dif.seconds / 60)}min ago'
        elif time_dif <= timedelta(hours=24):
            last_online = f'{round(time_dif.seconds / 3600)}hr ago'
        else:
            last_online = f'{time_dif.days} days ago'
        text = (
            f"\n\n\n\n🏷 Name: {profile.name if profile.name else "Not sat yet"}\n"
            f"🔢 Age: {profile.age if profile.age else "Not sat yet"}\n"
            f"👤 Gender: {profile.gender if profile.gender else "Not sat yet"}\n"
            f"📝 About: {profile.about if profile.about else "Not sat yet"}\n"
            f"🕰 Last seen: {last_online if profile.last_online else '"Not sat yet"'}"
            f"\n\nuser_id: /chaT_{profile.generated_id}"
            "\n\n\n"

        )
        #todo manage the query to send proper reply
        keyboard = [
            [
                InlineKeyboardButton('Direct MSG', callback_data=f"{self.msg_request_pattern}: {target_id}"),
                InlineKeyboardButton('Chat Request', callback_data=f"{self.button_starter_command} chat_request:{target_id}"),
            ],
            [
                InlineKeyboardButton('Like', callback_data=f"{self.button_starter_command} like:{target_id}"),
                InlineKeyboardButton('ADD Friend', callback_data=f"{self.button_starter_command} add_friend:{target_id}"),
            ],
            [
                InlineKeyboardButton('Block', callback_data=f"{self.button_starter_command} block:{target_id}"),
                InlineKeyboardButton('Report', callback_data=f"{self.button_starter_command} report:{target_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if profile.profile_photo:
            await update.message.reply_photo(
                photo=profile.profile_photo,
                caption=text,
                reply_markup=reply_markup

            )
        else:
            await update.message.reply_text(text,
                                            reply_markup=reply_markup)

    def load_profile(sefl, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # user_id = str(update.effective_chat.id)
        #todo switch db
        user_db.add_or_update_user(update.effective_user.id, context.user_data)
        user_db.get_user_data(update.effective_user.id, context.user_data)


        # try:
        #     with open("profiles/user_profiles.json", 'r') as file:
        #         data = json.load(file)
        # except FileNotFoundError:
        #     print('file not created')
        # user_data = data[user_id]
        # context.user_data['profile_photo'] = user_data['profile_photo']
        # context.user_data['name'] = user_data['name']
        # context.user_data['age'] = user_data['age']
        # context.user_data['gender'] = user_data['gender']
        # context.user_data['about'] = user_data['about']
        # context.user_data['location'] = user_data['location']

    def check_exist_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        context.user_data['user_id'] = str(update.effective_chat.id)
        user_db.add_or_update_user(update.effective_user.id, context.user_data)
        try:
            context.user_data['name']
        except KeyError:
            return False
        else:
            if context.user_data['name'] == "":
                return False
            else:
                return True
        # try:
        #     with open("profiles/user_profiles.json", 'r') as file:
        #         data = json.load(file)
        #         if user_id in data:
        #             self.load_profile(update, context)
        #             return True
        #         else:
        #
        #             return False
        #
        # except FileNotFoundError:
        #     with open("profiles/user_profiles.json", 'w') as file:
        #         return False
    #eh
    async def buttons(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        message_handler = UserMessage()
        query = update.callback_query
        if query.data.startswith(self.button_starter_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()
            if action == 'chat_request':
                await message_handler.chat_request(update, context, target_id)
            elif action == 'like':
                pass
            elif action == 'add_friend':
                pass
            elif action == 'block':
                pass
            elif action == 'report':
                pass
        elif query.data.startswith(self.msg_req_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()
            if action == 'accept':
                await self.chat_request_accepted(update, context, target_id)
            elif action == 'decline':
                await self.chat_reqeust_declined(update, context, target_id)
        elif query.data.startswith(self.my_profile_key_starter):
            action = query.data.split(':')[1].strip().lower()
            if action == 'edit':
                await self.show_my_profile_edit_mode(update, context)

    async def start_msg_request(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        target_id = query.data.split(':')[1].strip()
        context.user_data['request_from_id'] = target_id
        context.user_data['user_id'] = update.effective_user.id
        user_id = update.effective_user.id
        await context.bot.send_message(user_id, text='Plz send Your msg')
        return self.DIRECT_TEXT

    async def handle_direct_msg(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        target_id = context.user_data['request_from_id']
        msg = update.message.text
        if not msg:
            return
        if len(msg) > 250:
            return
        chat_db = ChatDatabase()

        if chat_db.add_requested_msg(user_id, target_id, msg):
            keyboard = [
                [
                    InlineKeyboardButton("Accept", callback_data=f"{self.msg_req_command}: accept: {user_id}"),
                    InlineKeyboardButton("Decline", callback_data=f"{self.msg_req_command}: decline: {user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Your message request has been sent. The recipient will be notified.")
            await context.bot.send_message(target_id, text=f"User /chaT_{user_id} wants to send you a message. Do you want to accept it?",
                                           reply_markup=reply_markup)
            return ConversationHandler.END
    async def chat_request_accepted(self, update:Update, context:ContextTypes.DEFAULT_TYPE, target_id):
        user_id = update.effective_user.id
        message_db = ChatDatabase()
        msgs= message_db.get_msg_requests_from_map(user_id, target_id)
        query = update.callback_query
        if msgs:
            for msg in msgs:
                await query.edit_message_text(f'Accepted: msgs from /chaT_{target_id}')
                await context.bot.send_message(user_id, text=f"/chaT_{target_id}: {msg}")
            await context.bot.send_message(target_id, text=f'/chaT_{user_id}:Received your Messages')
    async def chat_reqeust_declined(self, update:Update, context:ContextTypes.DEFAULT_TYPE, target_id):
        user_id = update.effective_user.id
        message_db = ChatDatabase()
        query = update.callback_query
        if message_db.clear_msg_requests_from_map(user_id, target_id):
            await query.edit_message_text(f'Declined: msgs from /chaT_{target_id}')
            await context.bot.send_message(target_id, text=f'/chaT_{user_id} declined ur direct messages')


    def get_all_handlers(self):
        return [
            self.get_profile_create_conversation_handler(),
            self.direct_msg_conversation_handler()


        ]

class Calculator:
    def __init__(self):
        self.ITEM, self.AMOUNT, self.CONST_FEE, self.SHOP_FEE, self.TEXT = range(5)
        self.calculate_command = 'calculator'

    def get_calculated_price_conversation_handler(self):
        return ConversationHandler(
            entry_points=[
                CommandHandler(self.calculate_command, self.start_calculation),
                CallbackQueryHandler(self.start_calculation, pattern=f"^{self.calculate_command}$")
            ],
            states={
                self.ITEM: [CallbackQueryHandler(self.handle_item)],
                self.AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_amount)],
                self.CONST_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_const_fee)],
                self.SHOP_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_shop_fee)],
                self.TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Calculator stopped')
        return ConversationHandler.END

    async def start_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Handle both Message (command) and CallbackQuery (button) updates
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message
        keyboard = [
            [InlineKeyboardButton('gold: 18karat', callback_data='18kr')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
        chat_id=message.chat.id,
        text="Let's calculate it. \nFirst what item we will calculate",
        reply_markup=reply_markup
    )
        return self.ITEM

    async def handle_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        #check item
        query = update.callback_query
        await query.answer()
        item = query.data
        if not item == '18kr':
            await query.edit_message_text("This item is not in our list plz Enter another:")
            return self.ITEM

        context.user_data['calculate_item'] = item

        await query.edit_message_text(f"OK! How much of {context.user_data['calculate_item']}:\n (gold: gram)")
        return self.AMOUNT
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            float(update.message.text)
        except ValueError:
            await update.message.reply_text(f"Plz enter the amount of {context.user_data['calculate_item']}\n gold: gram\nonly numbers")
            return self.AMOUNT
        else:
            context.user_data['amount'] = update.message.text

            await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
            return self.CONST_FEE

    async def handle_const_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            const_fee= float(update.message.text)
        except ValueError:
            await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
            return self.CONST_FEE
        else:
            if int(const_fee) not in range(100):
                await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
                return self.CONST_FEE
            context.user_data['const_fee'] = update.message.text

            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE

    async def handle_shop_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            shop_fee= float(update.message.text)
        except ValueError:
            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE
        else:
            if int(shop_fee) not in range(100):
                await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
                return self.CONST_FEE
            context.user_data['shop_fee'] = update.message.text

            await update.message.reply_text("Plz send text percentage: (1 to 100)")
            return self.TEXT

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            shop_fee= float(update.message.text)
        except ValueError:
            await update.message.reply_text("Plz send text percentage: (1 to 100)")
            return self.TEXT
        else:
            if int(shop_fee) not in range(100):
                await update.message.reply_text("Plz send text percentage: (1 to 100)")
                return self.TEXT
            context.user_data['text'] = update.message.text


            await self.show_calculated_result(update, context)

            return ConversationHandler.END

    async def show_calculated_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (f"item : {context.user_data["calculate_item"]} "
                f"\n amount: {context.user_data['amount']}"
                f"\n construction fee: {context.user_data['const_fee']}%"
                f"\n shop fee: {context.user_data['shop_fee']}%"
                f"\n text: {context.user_data['text']}%")

        await update.message.reply_text(text)

class TorobConversation:
    def __init__(self):
        self.NAME, self.PRICE, self.URL = range(3)
        self.EDIT_NAME =1
        self.EDIT_PRICE =1
        self.EDIT_URL=1
        self.DELETE=1
        self.query_add_pattern = 'add_new_torob_item'
        self.edit_price_pattern = 'torob_edit_price'
        self.edit_url_pattern='torob_edit_url'
        self.edit_name_pattern='torob_edit_name'
        self.delete_item_pattern='torob_delete_item'
        self.name = None
        self.price = None
        self.url = None
        self.db = TorobDb()

    def torob_add_handler(self):
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add, pattern=f'^{self.query_add_pattern}$')
            ],
            states= {
                self.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name)],
                self.PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_price)],
                self.URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
    def torob_edit_price_handler(self):
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_edit_price, pattern=f'^{self.edit_price_pattern}$')
            ],
            states={
                self.EDIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_price)],            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
    def torob_edit_url_handler(self):
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_edit_url, pattern=f'^{self.edit_url_pattern}$')
            ],
            states={
                self.EDIT_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_url)],                self.URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
    def torob_edit_name_handler(self):
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_edit_name, pattern=f'^{self.edit_name_pattern}$')
            ],
            states={
                self.EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_name)],            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
    def torob_delete_item(self):
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_delete_item, pattern=f'^{self.delete_item_pattern}$')
            ],
            states={
                self.DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_delete_item)],            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text('Opration cancelled')
        elif update.message:
            await update.message.reply_text('Operation cancelled')
        return ConversationHandler.END

    async def _send_fallback_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Helper method to safely send messages when normal replies fail."""
        try:
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text)
            elif update.message:
                await update.message.reply_text(text)
            elif 'chat_id' in context.user_data:
                await context.bot.send_message(
                    chat_id=context.user_data['chat_id'],
                    text=text
                )
        except Exception as e:
            print(f"⚠️ Failed to send fallback message: {e}")

    async def start_add(self, update: Update, context:ContextTypes.DEFAULT_TYPE):
       if not update.callback_query:
           return ConversationHandler.END
       await update.callback_query.answer()
       await update.callback_query.edit_message_text(
           f'Lets add new item to your torob list \n What is name of Item (less that 150)',

       )
       return self.NAME


    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        if not update.message or not update.message.text:
            await self._send_fallback_message(update, "Please send a text message")
            return self.NAME

        if len(update.message.text) > 150:
            await update.message.reply_text('Please enter a string with less than 150 characters!')
            return self.NAME

        self.name = update.message.text
        await update.message.reply_text(f"Plz enter highest price that ur interest in {self.name}")
        return self.PRICE

    async def handle_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            price = float(update.message.text)
            if price <= 0:
                await update.message.reply_text(
                    "❌ Price must be greater than 0."
                    "\n\nPlease enter the maximum price you're willing to pay:"
                )
                return self.PRICE
            self.price = price
        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid price (numbers only)."
                "\n\nExample: 1250000"
            )
            return self.PRICE
        else:

            await update.message.reply_text(f'plz gimme the url from torob that is for {self.name}')
            return self.URL

    def is_torob_url(self, url_string):
        try:
            result = urlparse(url_string)
            # Check if it's a valid URL (has scheme and netloc)
            if all([result.scheme, result.netloc]):
                # Check if 'torob.com' is in the netloc (domain) part
                return 'torob.com' in result.netloc
            return False
        except:
            return False

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        the_url = update.message.text
        if not self.is_torob_url(the_url):
            await update.message.reply_text('plz send a torob url ')
            return self.URL

        self.url = the_url
        if self.db.add_item(user_id, self.price, self.url, self.name):

            await update.message.reply_text(f'{self.name}: highest price{self.price}\n'
                                            f'with ur provided url added\n\n/start')
            self.price = None
            self.url = None
            self.name = None
            return ConversationHandler.END
        else:
            self.url = None
            await update.message.reply_text('plz send a torob url ')
            return self.URL

    async def start_delete_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id
        if not update.callback_query:
            return ConversationHandler.END
        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item do not belongs to You plz inter a valid item'
            )
            return ConversationHandler.END
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'Confirm delete with any world \n\nfor cancel type: /cancel'
        )
        return self.DELETE

    async def handle_delete_item(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        self.db.delete_item(item_id)
        await self.show_item_edit_options(update, context)
        return ConversationHandler.END



    async def start_edit_price(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id
        if not update.callback_query:
            return ConversationHandler.END
        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item do not belongs to You plz inter a valid item'
            )
            return ConversationHandler.END
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'plz enter new price'
        )
        return self.EDIT_PRICE
    async def handle_edit_price(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        try:
            price = float(update.message.text)
        except ValueError :
            await update.message.reply_text("plz enter price in numbers")
            return self.EDIT_PRICE
        else:
            self.db.update_preferred_price(item_id, price)
            await self.show_item_edit_options(update, context)
            return ConversationHandler.END


    async def start_edit_url(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id
        if not update.callback_query:
            return ConversationHandler.END
        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item do not belongs to You plz inter a valid item'
            )
            return ConversationHandler.END
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'plz enter new URL'
        )
        return self.EDIT_URL
    async def handle_edit_url(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id
        the_url = update.message.text
        if not self.is_torob_url(the_url):
            await update.message.reply_text('plz send a torob url ')
            return self.EDIT_URL
        if self.db.update_url(item_id, the_url):
            await self.show_item_edit_options(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text('plz send a torob url ')
            return self.EDIT_URL

    async def start_edit_name(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id
        if not update.callback_query:
            return ConversationHandler.END
        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item do not belongs to You plz inter a valid item'
            )
            return ConversationHandler.END
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'plz enter new name'
        )
        return self.EDIT_NAME
    async def handle_edit_name(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        item_id = context.user_data.get('editing_item_id', "")
        if not update.message or not update.message.text:
            await self._send_fallback_message(update, "Please send a text message")
            return self.EDIT_NAME

        if len(update.message.text) > 150:
            await update.message.reply_text('Please enter a string with less than 150 characters!')
            return self.EDIT_NAME

        if self.db.update_name(item_id, update.message.text):
            await self.show_item_edit_options(update, context)
            return ConversationHandler.END

    async def show_item_edit_options(self, update, context):
        item_id = context.user_data.get('editing_item_id', "")
        item_data = self.db.get_item_by_id(item_id)
        if item_data:
            keyboard = [
                [
                    InlineKeyboardButton('Edit Price', callback_data=f'{self.edit_price_pattern}'),
                    InlineKeyboardButton('Edit URL', callback_data=f'{self.edit_url_pattern}'),
                    InlineKeyboardButton('Edit Name', callback_data=f'{self.edit_name_pattern}')
                ],
                [InlineKeyboardButton('Delete', callback_data=f'{self.delete_item_pattern}')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if hasattr(update, 'message'):
                await update.message.reply_text(
                    f"✅ Item updated successfully!\n\n"
                    f"Item: {item_data.name_of_item}\n"
                    f"Current Highest Price: {item_data.user_preferred_price}\n\n"
                    f"Current URL: {item_data.torob_url}\n\n"
                    f"What would you like to edit next?",
                    reply_markup=reply_markup
                )
            else:
                await update.callback_query.edit_message_text(
                    f"✅ Item updated successfully!\n\n"
                    f"Item: {item_data.name_of_item}\n"
                    f"Current URL: {item_data.torob_url}\n\n"
                    f"What would you like to edit next?",
                    reply_markup=reply_markup
                )
        else:
            if hasattr(update, 'message'):
                await update.message.reply_text(
                    f"✅ Item Deleted successfully!\n\n/start")

            else:
                await update.callback_query.edit_message_text(
                    f"✅ Item Deleted successfully!\n\n/start")



    def get_all_handlers(self):
        return [
            self.torob_add_handler(),
            self.torob_edit_name_handler(),
            self.torob_edit_price_handler(),
            self.torob_edit_url_handler(),
            self.torob_delete_item(),
        ]


