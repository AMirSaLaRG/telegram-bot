from datetime import datetime, timedelta
import logging
from datetime import timedelta

from pyexpat.errors import messages
from telegram import (Update, InlineQueryResultArticle,
                      InputTextMessageContent, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, ReplyKeyboardRemove, )
from telegram.ext import (InlineQueryHandler, filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler,
                          ConversationHandler)
from data_base import UserDatabase, TorobDb, ChatDatabase
from urllib.parse import urlparse
from telegram_chat_handler import UserMessage

# Initialize DB instances
user_db = UserDatabase()



class Profile:
    """
    Handles user profile creation, viewing, and editing functionalities.
    Manages conversations for collecting user data like photo, name, age, gender, about, and location.
    Also handles displaying user profiles and direct message requests.
    """

    def __init__(self):
        """
        Initializes state constants for profile creation conversation and defines
        command/button patterns for profile-related interactions.
        """
        self.PHOTO, self.NAME, self.AGE, self.GENDER, self.ABOUT, self.LOCATION = range(6)
        self.create_commend = 'createprofile'
        self.button_starter_command = 'start_profile_buttons:'
        self.DIRECT_TEXT = 1  # State for direct message input
        self.msg_request_pattern = 'user_wants_to_send_direct_msg'
        self.msg_req_command = 'the_msg_req_ask'
        self.my_profile_key_starter = 'my_Profile_command_starter'

    def get_profile_create_conversation_handler(self):
        """
        Defines and returns the ConversationHandler for profile creation.
        It specifies entry points, states, and fallbacks for the conversation flow.
        """
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
        """
        Defines and returns the ConversationHandler for sending direct messages.
        It handles the start of a message request and the text input for the message.
        """
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_msg_request, pattern=f'^{self.msg_request_pattern}')],
            states={
                self.DIRECT_TEXT: [MessageHandler(filters.TEXT, self.handle_direct_msg)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]

        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Cancels the current conversation and sends a cancellation message.
        """
        await update.message.reply_text('Profile creation cancelled')
        return ConversationHandler.END

    async def start_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the profile creation conversation. Asks the user to send their photo.
        """
        context.user_data['user_id'] = update.effective_user.id
        await update.message.reply_text(
            "Lets create your profile.\n First send me your photo",
            reply_markup=ReplyKeyboardRemove()  # Removes the custom keyboard
        )
        return self.PHOTO

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the photo input during profile creation. Stores the file_id of the highest
        resolution photo and prompts for the user's name.
        """
        # Check if a photo was actually sent
        if not update.message.photo:
            await update.message.reply_text("plz send your photo!")
            return self.PHOTO

        # Store the file_id of the highest resolution photo
        photo_file = await update.message.photo[-1].get_file()
        context.user_data['profile_photo'] = photo_file.file_id

        await update.message.reply_text("Great!! \n now send me your name")
        return self.NAME

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the name input during profile creation. Stores the name and prompts for age.
        """
        context.user_data['name'] = update.message.text

        await update.message.reply_text("What's your age?")
        return self.AGE

    async def handle_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the age input during profile creation. Validates age (13-120),
        stores it, and prompts for gender with a custom keyboard.
        """
        try:
            age = int(update.message.text)
            if age < 13 or age > 120:
                await update.message.reply_text(
                    "⚠️ Please enter a valid age between 13-120."
                    "\n\nHow old are you?"
                )
                return self.AGE  # Stay in AGE state
            context.user_data['age'] = age
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(
                "❌ That doesn't look like a valid age."
                "\n\nPlease enter your age as a number (e.g. 25):"
            )
            return self.AGE  # Stay in AGE state

        # Create gender selection keyboard
        reply_keyboard = [["Male"], ["Female"], ["Other"]]
        await update.message.reply_text(
            "Select your gender:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,  # Keyboard disappears after one use
                input_field_placeholder="Your gender?"
            )
        )
        return self.GENDER

    async def handle_gender(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the gender input during profile creation. Stores the gender and
        prompts for the 'about' section.
        """
        context.user_data['gender'] = update.message.text

        await update.message.reply_text(
            "Tell me something about yourself (max 200 characters):",
            reply_markup=ReplyKeyboardRemove()  # Removes the custom keyboard
        )
        return self.ABOUT

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the 'about' text input during profile creation. Validates length,
        stores the text, and prompts for location with a "Share Location" button.
        """
        if len(update.message.text) > 200:
            await update.message.reply_text("Please keep it under 200 characters!")
            return self.ABOUT  # Stay in ABOUT state

        context.user_data['about'] = update.message.text

        # Request location with a button that triggers location sharing
        reply_keyboard = [[KeyboardButton("Share Location", request_location=True)]]
        await update.message.reply_text(
            "Finally, share your location:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                resize_keyboard=True,  # Adjusts keyboard size based on content
            )
        )
        return self.LOCATION

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the location input during profile creation. Stores latitude and longitude,
        saves the complete profile to the database, and displays the user's profile.
        """
        location = update.message.location
        context.user_data['location'] = (location.latitude, location.longitude)
        context.user_data['latitude'] = context.user_data['location'][0]
        context.user_data['longitude'] = context.user_data['location'][1]

        # Save the complete profile to the database
        user_db.add_or_update_user(update.effective_user.id, context.user_data)

        # Display the newly created/updated profile
        await self.show_my_profile(update, context)

        return ConversationHandler.END  # End the conversation

    async def show_my_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays the current user's profile information, including photo, name, age,
        gender, 'about' text, last online status, and a generated user ID.
        Provides inline buttons for editing profile and other actions.
        """
        self.load_profile(update, context)  # Ensure user_data is loaded/updated from DB
        user_id = update.effective_user.id

        profile = user_db.get_user_information(user_id)  # Retrieve profile from DB

        # Calculate and format last online status
        time_dif = datetime.now() - profile.last_online
        if time_dif <= timedelta(minutes=5):
            last_online = 'Online'
        elif time_dif < timedelta(hours=1):
            last_online = f'{round(time_dif.seconds / 60)}min ago'
        elif time_dif <= timedelta(hours=24):
            last_online = f'{round(time_dif.seconds / 3600)}hr ago'
        else:
            last_online = f'{time_dif.days} days ago'

        # Construct the profile display text
        text = (
            f"\n\n\n\n🏷 Name: {profile.name if profile.name else "Not sat yet"}\n"
            f"🔢 Age: {profile.age if profile.age else "Not sat yet"}\n"
            f"👤 Gender: {profile.gender if profile.gender else "Not sat yet"}\n"
            f"📝 About: {profile.about if profile.about else "Not sat yet"}\n"
            f"🕰 online: {last_online if profile.last_online else '"Long time ago"'}"
            f"\n\nuser_id: /chaT_{profile.generated_id}"
            "\n\n\n"

        )

        # Define inline keyboard buttons for profile actions
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

        # Send photo with caption or just text if no photo exists
        if profile.profile_photo:
            await update.message.reply_photo(
                photo=profile.profile_photo,
                caption=text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(text)

    async def show_my_profile_edit_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Switches the 'My Profile' view to an edit mode, presenting buttons for
        specific profile field edits (Name, About, City, Photo).
        """
        self.load_profile(update, context)  # Ensure user data is up-to-date

        # Define inline keyboard buttons for specific edit actions
        keyboard = [
            [
                InlineKeyboardButton('Edit Name', callback_data='edit'),
                InlineKeyboardButton('Edit About', callback_data='update location')
                # Mislabeled, should be specific action
            ],
            [
                InlineKeyboardButton('Edit City', callback_data='liked'),  # Mislabeled
                InlineKeyboardButton('Edit Photo', callback_data="friends")  # Mislabeled
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query  # Get the callback query that triggered this

        # Edit the original message's reply markup to show new buttons
        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )

    async def show_target_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        """
        Displays the profile information of a target user (not the current user).
        Includes options to send direct messages, chat requests, like, add friend, block, or report.

        Args:
            update (Update): The Telegram Update object.
            context (ContextTypes.DEFAULT_TYPE): The context object for the current update.
            target_id (int): The user ID of the target profile to display.
        """
        self.load_profile(update, context)  # Ensure current user's data is loaded

        profile = user_db.get_user_information(target_id)  # Retrieve target user's profile from DB

        # Calculate and format last online status for the target user
        time_dif = datetime.now() - profile.last_online
        if time_dif <= timedelta(minutes=5):
            last_online = 'Online'
        elif time_dif < timedelta(hours=1):
            last_online = f'{round(time_dif.seconds / 60)}min ago'
        elif time_dif <= timedelta(hours=24):
            last_online = f'{round(time_dif.seconds / 3600)}hr ago'
        else:
            last_online = f'{time_dif.days} days ago'

        # Construct the target profile display text
        text = (
            f"\n\n\n\n🏷 Name: {profile.name if profile.name else "Not sat yet"}\n"
            f"🔢 Age: {profile.age if profile.age else "Not sat yet"}\n"
            f"👤 Gender: {profile.gender if profile.gender else "Not sat yet"}\n"
            f"📝 About: {profile.about if profile.about else "Not sat yet"}\n"
            f"🕰 Last seen: {last_online if profile.last_online else '"Not sat yet"'}"
            f"\n\nuser_id: /chaT_{profile.generated_id}"  # Display generated ID for public sharing
            "\n\n\n"

        )

        # Define inline keyboard buttons for interacting with the target user
        keyboard = [
            [
                InlineKeyboardButton('Direct MSG', callback_data=f"{self.msg_request_pattern}: {target_id}"),
                InlineKeyboardButton('Chat Request',
                                     callback_data=f"{self.button_starter_command} chat_request:{target_id}"),
            ],
            [
                InlineKeyboardButton('Like', callback_data=f"{self.button_starter_command} like:{target_id}"),
                InlineKeyboardButton('ADD Friend',
                                     callback_data=f"{self.button_starter_command} add_friend:{target_id}"),
            ],
            [
                InlineKeyboardButton('Block', callback_data=f"{self.button_starter_command} block:{target_id}"),
                InlineKeyboardButton('Report', callback_data=f"{self.button_starter_command} report:{target_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send photo with caption or just text if no photo exists for the target profile
        if profile.profile_photo:
            await update.message.reply_photo(
                photo=profile.profile_photo,
                caption=text,
                reply_markup=reply_markup

            )
        else:
            await update.message.reply_text(text,
                                            reply_markup=reply_markup)

    def load_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Loads the user's profile data from the database into `context.user_data`.
        Ensures the user exists in the database and updates their `last_online` status.
        """
        # user_id = str(update.effective_chat.id) # Original comment, now using effective_user.id
        user_db.add_or_update_user(update.effective_user.id,
                                   context.user_data)  # Ensures user exists and updates last_online
        user_db.get_user_data(update.effective_user.id, context.user_data)  # Populates context.user_data

        # Original commented out code for JSON file-based profile loading (not used with current DB)
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
        """
        Checks if a user's profile exists based on their 'name' in `context.user_data`.
        This method ensures the user's entry exists in the database first.

        Args:
            update (Update): The Telegram Update object.
            context (ContextTypes.DEFAULT_TYPE): The context object for the current update.

        Returns:
            bool: True if the user has a non-empty 'name' in their profile, False otherwise.
        """
        context.user_data['user_id'] = str(update.effective_chat.id)  # Ensure user_id is in context
        user_db.add_or_update_user(update.effective_user.id, context.user_data)  # Ensure user record exists
        try:
            # Check if 'name' key exists in user_data
            context.user_data['name']
        except KeyError:
            return False  # 'name' key not found
        else:
            # Check if 'name' value is not an empty string
            if context.user_data['name'] == "":
                return False
            else:
                return True
        # Original commented out code for JSON file-based profile checking (not used with current DB)
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

    # eh
    async def buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles callbacks from inline keyboard buttons related to profile interactions
        (e.g., chat requests, direct messages, likes, blocks).
        Routes the actions based on the callback data pattern.
        """
        message_handler = UserMessage()  # Instance of UserMessage for chat-related actions
        query = update.callback_query

        # Handle buttons starting with my_profile_key_starter (e.g., 'edit', 'update location')
        if query.data.startswith(self.button_starter_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()  # Target ID from callback data
            if action == 'chat_request':
                await message_handler.chat_request(update, context, target_id)
            elif action == 'like':
                pass  # Placeholder for like functionality
            elif action == 'add_friend':
                pass  # Placeholder for add friend functionality
            elif action == 'block':
                pass  # Placeholder for block functionality
            elif action == 'report':
                pass  # Placeholder for report functionality
        # Handle buttons related to message requests (accept/decline)
        elif query.data.startswith(self.msg_req_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()
            if action == 'accept':
                await self.chat_request_accepted(update, context, target_id)
            elif action == 'decline':
                await self.chat_reqeust_declined(update, context, target_id)
        # Handle buttons specific to 'My Profile' edit options
        elif query.data.startswith(self.my_profile_key_starter):
            action = query.data.split(':')[1].strip().lower()
            if action == 'edit':
                await self.show_my_profile_edit_mode(update, context)

    async def start_msg_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Initiates the direct message request conversation.
        Stores the target user's ID and prompts the user to send their message.
        """
        query = update.callback_query
        target_id = query.data.split(':')[1].strip()  # Extract target_id from callback data
        context.user_data['request_from_id'] = target_id  # Store target ID in user_data
        context.user_data['user_id'] = update.effective_user.id  # Ensure current user_id is in context
        user_id = update.effective_user.id
        await context.bot.send_message(user_id, text='Plz send Your msg')
        return self.DIRECT_TEXT  # Move to the state for direct message text input

    async def handle_direct_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the text input for a direct message request.
        Validates message length, adds it as a 'requested' message to the database,
        and notifies both sender and receiver.
        """
        user_id = update.effective_user.id
        target_id = context.user_data['request_from_id']  # Retrieve target ID
        msg = update.message.text

        # Basic message validation
        if not msg:
            return ConversationHandler.END  # End conversation if no message text
        if len(msg) > 250:
            # Maybe send a warning message and stay in the state
            await update.message.reply_text("Message is too long. Please keep it under 250 characters.")
            return self.DIRECT_TEXT

        chat_db = ChatDatabase()  # Instance of ChatDatabase

        # Attempt to add the message as a requested message in the database
        if chat_db.add_requested_msg(user_id, target_id, msg):
            # Create inline keyboard for recipient to accept or decline the message request
            keyboard = [
                [
                    InlineKeyboardButton("Accept", callback_data=f"{self.msg_req_command}: accept: {user_id}"),
                    InlineKeyboardButton("Decline", callback_data=f"{self.msg_req_command}: decline: {user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Notify the sender that their request has been sent
            await update.message.reply_text("Your message request has been sent. The recipient will be notified.")
            # Notify the recipient with the message request and action buttons
            await context.bot.send_message(target_id,
                                           text=f"User /chaT_{user_id} wants to send you a message. Do you want to accept it?",
                                           reply_markup=reply_markup)
            return ConversationHandler.END  # End conversation
        else:
            # Handle case where message could not be added (e.g., DB error)
            await update.message.reply_text("There was an issue sending your message request. Please try again.")
            return ConversationHandler.END

    async def chat_request_accepted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        """
        Handles the acceptance of a chat request. Retrieves and sends the requested messages
        from the sender to the accepting user, and notifies the sender.

        Args:
            update (Update): The Telegram Update object (contains callback_query).
            context (ContextTypes.DEFAULT_TYPE): The context object.
            target_id (int): The user ID of the sender whose messages are being accepted.
        """
        user_id = update.effective_user.id
        message_db = ChatDatabase()

        # Get requested messages from the database
        msgs = message_db.get_msg_requests_from_map(user_id, target_id)
        query = update.callback_query  # The callback query that triggered this action

        if msgs:
            await query.edit_message_text(f'Accepted: msgs from /chaT_{target_id}')  # Edit original button message
            for msg in msgs:
                await context.bot.send_message(user_id,
                                               text=f"/chaT_{target_id}: {msg}")  # Send each message to the accepting user
            await context.bot.send_message(target_id, text=f'/chaT_{user_id}:Received your Messages')  # Notify sender
        else:
            await query.edit_message_text(f'No messages to retrieve from /chaT_{target_id}')  # No messages found

        # Consider ending the conversation or offering next steps here

    async def chat_reqeust_declined(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        """
        Handles the declining of a chat request. Clears the requested messages
        from the database and notifies both the declining user and the sender.

        Args:
            update (Update): The Telegram Update object (contains callback_query).
            context (ContextTypes.DEFAULT_TYPE): The context object.
            target_id (int): The user ID of the sender whose messages are being declined.
        """
        user_id = update.effective_user.id
        message_db = ChatDatabase()
        query = update.callback_query  # The callback query that triggered this action

        # Attempt to clear requested messages from the database
        if message_db.clear_msg_requests_from_map(user_id, target_id):
            await query.edit_message_text(f'Declined: msgs from /chaT_{target_id}')  # Edit original button message
            await context.bot.send_message(target_id,
                                           text=f'/chaT_{user_id} declined ur direct messages')  # Notify sender
        else:
            await query.edit_message_text(
                f'Failed to decline or no messages to clear from /chaT_{target_id}')  # Error or no messages

    def get_all_handlers(self) -> list:
        """
        Returns a list of all ConversationHandlers managed by the Profile class.
        This is used to register them with the Telegram bot application.
        """
        return [
            self.get_profile_create_conversation_handler(),
            self.direct_msg_conversation_handler()
        ]


class Calculator:
    """
    Handles a conversation for calculating prices, particularly for gold.
    Guides the user through inputs like item type, amount, construction fee, shop fee, and text fee.
    """

    def __init__(self):
        """
        Initializes state constants for the calculation conversation and defines
        the command/pattern for starting the calculator.
        """
        self.ITEM, self.AMOUNT, self.CONST_FEE, self.SHOP_FEE, self.TEXT = range(5)
        self.calculate_command = 'calculator'

    def get_calculated_price_conversation_handler(self):
        """
        Defines and returns the ConversationHandler for the price calculation feature.
        It specifies entry points, states, and fallbacks for the conversation flow.
        """
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
        """
        Cancels the current calculation conversation and sends a cancellation message.
        """
        # Checks if update is a message or a callback query to reply appropriately
        if update.message:
            await update.message.reply_text('Calculator stopped')
        elif update.callback_query:
            await update.callback_query.answer()  # Answer the callback query to remove loading indicator
            await update.callback_query.edit_message_text('Calculator stopped')  # Edit message to confirm cancellation
        return ConversationHandler.END

    async def start_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the price calculation conversation. Presents initial item options.
        """
        # Handle both Message (command) and CallbackQuery (button) updates
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message

        # Define inline keyboard with item options
        keyboard = [
            [InlineKeyboardButton('gold: 18karat', callback_data='18kr')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message with item options
        await context.bot.send_message(
            chat_id=message.chat.id,
            text="Let's calculate it. \nFirst what item we will calculate",
            reply_markup=reply_markup
        )
        return self.ITEM  # Move to the ITEM state

    async def handle_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the selected item for calculation. Validates the item and
        prompts for the amount.
        """
        query = update.callback_query
        await query.answer()  # Answer the callback query to remove loading indicator
        item = query.data

        # Validate selected item
        if not item == '18kr':
            await query.edit_message_text("This item is not in our list plz Enter another:")
            return self.ITEM  # Stay in ITEM state

        context.user_data['calculate_item'] = item  # Store selected item

        await query.edit_message_text(f"OK! How much of {context.user_data['calculate_item']}:\n (gold: gram)")
        return self.AMOUNT  # Move to the AMOUNT state

    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the amount input for the selected item. Validates if it's a number
        and prompts for the construction fee percentage.
        """
        try:
            float(update.message.text)  # Attempt to convert input to float for validation
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(
                f"Plz enter the amount of {context.user_data['calculate_item']}\n gold: gram\nonly numbers")
            return self.AMOUNT  # Stay in AMOUNT state
        else:
            context.user_data['amount'] = update.message.text  # Store amount as text (can be converted to float later)

            await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
            return self.CONST_FEE  # Move to the CONST_FEE state

    async def handle_const_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the construction fee percentage input. Validates the percentage (1-100)
        and prompts for the shop fee percentage.
        """
        try:
            const_fee = float(update.message.text)  # Attempt to convert input to float
        except ValueError:  # If input is not a valid number
            await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
            return self.CONST_FEE  # Stay in CONST_FEE state
        else:
            if not 1 <= int(const_fee) <= 100:  # Check if percentage is within range
                await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
                return self.CONST_FEE  # Stay in CONST_FEE state
            context.user_data['const_fee'] = update.message.text  # Store as text

            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE  # Move to the SHOP_FEE state

    async def handle_shop_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the shop fee percentage input. Validates the percentage (1-100)
        and prompts for the text percentage.
        """
        try:
            shop_fee = float(update.message.text)  # Attempt to convert input to float
        except ValueError:  # If input is not a valid number
            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE  # Stay in SHOP_FEE state
        else:
            if not 1 <= int(shop_fee) <= 100:  # Check if percentage is within range
                await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
                return self.CONST_FEE  # Should be SHOP_FEE (typo in original code), staying in current state
            context.user_data['shop_fee'] = update.message.text  # Store as text

            await update.message.reply_text("Plz send text percentage: (1 to 100)")
            return self.TEXT  # Move to the TEXT state

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the text percentage input. Validates the percentage (1-100)
        and then displays the calculated result.
        """
        try:
            text_fee = float(update.message.text)  # Corrected variable name for clarity
        except ValueError:  # If input is not a valid number
            await update.message.reply_text("Plz send text percentage: (1 to 100)")
            return self.TEXT  # Stay in TEXT state
        else:
            if not 1 <= int(text_fee) <= 100:  # Check if percentage is within range
                await update.message.reply_text("Plz send text percentage: (1 to 100)")
                return self.TEXT  # Stay in TEXT state
            context.user_data['text'] = update.message.text  # Store as text

            await self.show_calculated_result(update, context)  # Display results

            return ConversationHandler.END  # End the conversation

    async def show_calculated_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays the summary of the calculated price based on user inputs.
        """
        # Construct the result text from stored user data
        text = (f"item : {context.user_data["calculate_item"]} "
                f"\n amount: {context.user_data['amount']}"
                f"\n construction fee: {context.user_data['const_fee']}%"
                f"\n shop fee: {context.user_data['shop_fee']}%"
                f"\n text: {context.user_data['text']}%")

        await update.message.reply_text(text)


class TorobConversation:
    """
    Manages conversations for adding, editing, and deleting items tracked on Torob.
    Handles user input for item name, preferred price, and URL.
    """

    def __init__(self):
        """
        Initializes state constants for Torob item management conversations and defines
        callback query patterns for various actions.
        """
        self.NAME, self.PRICE, self.URL = range(3)  # States for adding new item
        self.EDIT_NAME = 1  # State for editing item name
        self.EDIT_PRICE = 1  # State for editing item price
        self.EDIT_URL = 1  # State for editing item URL
        self.DELETE = 1  # State for deleting an item
        self.query_add_pattern = 'add_new_torob_item'
        self.edit_price_pattern = 'torob_edit_price'
        self.edit_url_pattern = 'torob_edit_url'
        self.edit_name_pattern = 'torob_edit_name'
        self.delete_item_pattern = 'torob_delete_item'
        self.name = None  # Temporary storage for item name during conversation
        self.price = None  # Temporary storage for item price during conversation
        self.url = None  # Temporary storage for item URL during conversation
        self.db = TorobDb()  # Instance of TorobDb for database operations

    def torob_add_handler(self):
        """
        Defines and returns the ConversationHandler for adding a new Torob item.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add, pattern=f'^{self.query_add_pattern}$')
            ],
            states={
                self.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name)],
                self.PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_price)],
                self.URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    def torob_edit_price_handler(self):
        """
        Defines and returns the ConversationHandler for editing a Torob item's price.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_edit_price, pattern=f'^{self.edit_price_pattern}$')
            ],
            states={
                self.EDIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_price)], },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    def torob_edit_url_handler(self):
        """
        Defines and returns the ConversationHandler for editing a Torob item's URL.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_edit_url, pattern=f'^{self.edit_url_pattern}$')
            ],
            states={
                self.EDIT_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_url)],
                # self.URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)], # This line seems like a duplicate state entry or a leftover
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    def torob_edit_name_handler(self):
        """
        Defines and returns the ConversationHandler for editing a Torob item's name.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_edit_name, pattern=f'^{self.edit_name_pattern}$')
            ],
            states={
                self.EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_name)], },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    def torob_delete_item(self):
        """
        Defines and returns the ConversationHandler for deleting a Torob item.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_delete_item, pattern=f'^{self.delete_item_pattern}$')
            ],
            states={
                self.DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_delete_item)], },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Cancels the current Torob conversation (add/edit/delete) and sends a cancellation message.
        """
        if update.callback_query:
            await update.callback_query.answer()  # Acknowledge the callback query
            await update.callback_query.edit_message_text('Operation cancelled')
        elif update.message:
            await update.message.reply_text('Operation cancelled')
        return ConversationHandler.END  # End the conversation

    async def _send_fallback_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """
        Helper method to safely send messages when normal replies or edits might fail.
        Attempts to reply via callback_query, then message, then direct to chat_id.
        """
        try:
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text)
            elif update.message:
                await update.message.reply_text(text)
            elif 'chat_id' in context.user_data:  # Fallback if neither callback_query nor message exists
                await context.bot.send_message(
                    chat_id=context.user_data['chat_id'],
                    text=text
                )
        except Exception as e:
            print(f"⚠️ Failed to send fallback message: {e}")

    async def start_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation to add a new Torob item. Prompts for the item's name.
        """
        if not update.callback_query:  # Ensure it's triggered by a callback query
            return ConversationHandler.END
        await update.callback_query.answer()  # Acknowledge the callback query
        await update.callback_query.edit_message_text(
            f'Lets add new item to your torob list \n What is name of Item (less that 150)',
        )
        return self.NAME  # Move to the NAME state

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the item name input during the add item conversation.
        Validates length and prompts for the preferred price.
        """
        if not update.message or not update.message.text:
            await self._send_fallback_message(update, context, "Please send a text message")
            return self.NAME  # Stay in NAME state

        if len(update.message.text) > 150:  # Validate name length
            await update.message.reply_text('Please enter a string with less than 150 characters!')
            return self.NAME  # Stay in NAME state

        self.name = update.message.text  # Store the name temporarily
        await update.message.reply_text(f"Plz enter highest price that ur interest in {self.name}")
        return self.PRICE  # Move to the PRICE state

    async def handle_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the preferred price input during the add item conversation.
        Validates if it's a positive number and prompts for the Torob URL.
        """
        try:
            price = float(update.message.text)
            if price <= 0:  # Price must be positive
                await update.message.reply_text(
                    "❌ Price must be greater than 0."
                    "\n\nPlease enter the maximum price you're willing to pay:"
                )
                return self.PRICE  # Stay in PRICE state
            self.price = price  # Store the price temporarily
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(
                "❌ Please enter a valid price (numbers only)."
                "\n\nExample: 1250000"
            )
            return self.PRICE  # Stay in PRICE state
        else:  # If price is valid
            await update.message.reply_text(f'plz gimme the url from torob that is for {self.name}')
            return self.URL  # Move to the URL state

    def is_torob_url(self, url_string: str) -> bool:
        """
        Helper method to validate if a given string is a valid URL and specifically from 'torob.com'.

        Args:
            url_string (str): The URL string to validate.

        Returns:
            bool: True if the URL is valid and contains 'torob.com', False otherwise.
        """
        try:
            result = urlparse(url_string)
            # Check if it's a valid URL (has scheme like http/https and a network location/domain)
            if all([result.scheme, result.netloc]):
                # Check if 'torob.com' is in the netloc (domain) part
                return 'torob.com' in result.netloc
            return False
        except Exception as e:  # Catch any parsing errors
            print(f'torob conversation: {e}')
            return False

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the Torob URL input during the add item conversation.
        Validates the URL, adds the item to the database, and ends the conversation.
        """
        user_id = update.effective_user.id
        the_url = update.message.text

        if not self.is_torob_url(the_url):  # Validate if it's a valid Torob URL
            await update.message.reply_text('plz send a torob url ')
            return self.URL  # Stay in URL state

        self.url = the_url  # Store the URL temporarily

        # Attempt to add the item to the database
        print(self.price, self.url, self.name)
        if self.db.add_item(user_id, self.price, self.url, self.name):
            await update.message.reply_text(f'{self.name}: highest price {self.price}\n'
                                            f'with ur provided url added\n\n/start')
            # Clear temporary stored data
            self.price = None
            self.url = None
            self.name = None
            return ConversationHandler.END  # End the conversation
        else:  # If item could not be added (e.g., DB error)
            self.url = None  # Clear URL, might be invalid
            await update.message.reply_text('Failed to add item. Please ensure the URL is valid and try again.')
            return self.URL  # Stay in URL state

    async def start_delete_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation for deleting a Torob item.
        Confirms user ownership and prompts for confirmation.
        """
        item_id = context.user_data.get('editing_item_id', "")  # Get item ID from user_data
        user_id = update.effective_user.id

        if not update.callback_query:  # Ensure triggered by callback
            return ConversationHandler.END

        # Check if the user owns this item
        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item does not belong to you. Please enter a valid item ID.'
            )
            return ConversationHandler.END  # End if not owner

        await update.callback_query.answer()  # Acknowledge callback
        await update.callback_query.edit_message_text(
            f'Confirm delete with any word \n\nfor cancel type: /cancel'
        )
        return self.DELETE  # Move to the DELETE state for confirmation

    async def handle_delete_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the confirmation for deleting a Torob item. Deletes the item from DB
        and shows updated item options.
        """
        item_id = context.user_data.get('editing_item_id', "")
        self.db.delete_item(item_id)  # Delete the item from the database
        await self.show_item_edit_options(update, context)  # Show updated options (will indicate deletion)
        return ConversationHandler.END  # End the conversation

    async def start_edit_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation for editing a Torob item's preferred price.
        Confirms user ownership and prompts for the new price.
        """
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id

        if not update.callback_query:
            return ConversationHandler.END

        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item does not belong to you. Please enter a valid item ID.'
            )
            return ConversationHandler.END

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'Please enter new price'
        )
        return self.EDIT_PRICE  # Move to the EDIT_PRICE state

    async def handle_edit_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the new price input for editing a Torob item.
        Validates the price, updates it in the DB, and shows updated item options.
        """
        item_id = context.user_data.get('editing_item_id', "")
        try:
            price = float(update.message.text)  # Convert input to float
        except ValueError:  # If input is not a valid number
            await update.message.reply_text("Please enter price in numbers")
            return self.EDIT_PRICE  # Stay in EDIT_PRICE state
        else:
            self.db.update_preferred_price(item_id, price)  # Update price in DB
            await self.show_item_edit_options(update, context)  # Show updated options
            return ConversationHandler.END  # End the conversation

    async def start_edit_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation for editing a Torob item's URL.
        Confirms user ownership and prompts for the new URL.
        """
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id

        if not update.callback_query:
            return ConversationHandler.END

        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item does not belong to you. Please enter a valid item ID.'
            )
            return ConversationHandler.END

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'Please enter new URL'
        )
        return self.EDIT_URL  # Move to the EDIT_URL state

    async def handle_edit_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the new URL input for editing a Torob item.
        Validates the URL, updates it in the DB, and shows updated item options.
        """
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id  # user_id is not used here, but was in original for check_ownership
        the_url = update.message.text

        if not self.is_torob_url(the_url):  # Validate if it's a valid Torob URL
            await update.message.reply_text('Please send a torob url ')
            return self.EDIT_URL  # Stay in EDIT_URL state

        if self.db.update_url(item_id, the_url):  # Update URL in DB
            await self.show_item_edit_options(update, context)  # Show updated options
            return ConversationHandler.END  # End the conversation
        else:  # If update failed
            await update.message.reply_text('Failed to update URL. Please try again with a valid Torob URL.')
            return self.EDIT_URL  # Stay in EDIT_URL state

    async def start_edit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation for editing a Torob item's name.
        Confirms user ownership and prompts for the new name.
        """
        item_id = context.user_data.get('editing_item_id', "")
        user_id = update.effective_user.id

        if not update.callback_query:
            return ConversationHandler.END

        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                f'This item does not belong to you. Please enter a valid item ID.'
            )
            return ConversationHandler.END

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f'Please enter new name'
        )
        return self.EDIT_NAME  # Move to the EDIT_NAME state

    async def handle_edit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the new name input for editing a Torob item.
        Validates length, updates it in the DB, and shows updated item options.
        """
        item_id = context.user_data.get('editing_item_id', "")

        if not update.message or not update.message.text:
            await self._send_fallback_message(update, context, "Please send a text message")
            return self.EDIT_NAME  # Stay in EDIT_NAME state

        if len(update.message.text) > 150:  # Validate name length
            await update.message.reply_text('Please enter a string with less than 150 characters!')
            return self.EDIT_NAME  # Stay in EDIT_NAME state

        if self.db.update_name(item_id, update.message.text):  # Update name in DB
            await self.show_item_edit_options(update, context)  # Show updated options
            return ConversationHandler.END  # End the conversation
        else:
            await update.message.reply_text('Failed to update name. Please try again.')
            return self.EDIT_NAME  # Stay in EDIT_NAME state

    async def show_item_edit_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays the current details of an item after an edit operation (or deletion),
        along with inline buttons for further editing or deletion.
        """
        item_id = context.user_data.get('editing_item_id', "")
        item_data = self.db.get_item_by_id(item_id)  # Retrieve the item data

        if item_data:  # If the item still exists (i.e., not just deleted)
            # Define inline keyboard with edit/delete options
            keyboard = [
                [
                    InlineKeyboardButton('Edit Price', callback_data=f'{self.edit_price_pattern}'),
                    InlineKeyboardButton('Edit URL', callback_data=f'{self.edit_url_pattern}'),
                    InlineKeyboardButton('Edit Name', callback_data=f'{self.edit_name_pattern}')
                ],
                [InlineKeyboardButton('Delete', callback_data=f'{self.delete_item_pattern}')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Check if the update is from a message or callback_query to reply appropriately
            if hasattr(update, 'message'):
                await update.message.reply_text(
                    f"✅ Item updated successfully!\n\n"
                    f"Item: {item_data.name_of_item}\n"
                    f"Current Highest Price: {item_data.user_preferred_price}\n\n"
                    f"Current URL: {item_data.torob_url}\n\n"
                    f"What would you like to edit next?",
                    reply_markup=reply_markup
                )
            else:  # Assuming it's a callback query
                await update.callback_query.edit_message_text(
                    f"✅ Item updated successfully!\n\n"
                    f"Item: {item_data.name_of_item}\n"
                    f"Current URL: {item_data.torob_url}\n\n"  # Original text was missing price, added for consistency
                    f"Current Highest Price: {item_data.user_preferred_price}\n\n"
                    f"What would you like to edit next?",
                    reply_markup=reply_markup
                )
        else:  # If the item no longer exists (presumably deleted)
            if hasattr(update, 'message'):
                await update.message.reply_text(
                    f"✅ Item Deleted successfully!\n\n/start")  # Notify deletion and suggest /start

            else:  # Assuming it's a callback query
                await update.callback_query.edit_message_text(
                    f"✅ Item Deleted successfully!\n\n/start")  # Notify deletion and suggest /start

    def get_all_handlers(self) -> list:
        """
        Returns a list of all ConversationHandlers managed by the TorobConversation class.
        This is used to register them with the Telegram bot application.
        """
        return [
            self.torob_add_handler(),
            self.torob_edit_name_handler(),
            self.torob_edit_price_handler(),
            self.torob_edit_url_handler(),
            self.torob_delete_item(),
        ]