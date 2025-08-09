from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove, InputMediaPhoto
from telegram.error import BadRequest
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CommandHandler, \
    CallbackQueryHandler

from bot.handlers.telegram_chat_handler import UserMessage
from bot.handlers.intraction import track_user_interaction

from bot.db.database import UserDatabase, ChatDatabase, RelationshipManager
from bot.handlers.relationship import RelationshipHandler


from bot.utils.messages_manager import messages as msg
# messages = msg(language=context.user_data['lan'])

from bot.utils.messages_manager import languages





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
        self.EDIT_NAME, self.EDIT_ABOUT, self.EDIT_CITY, self.EDIT_PHOTO, self.EDIT_LOCATION = range(6, 11)
        self.create_commend = 'createprofile'
        self.button_starter_command = 'start_profile_buttons:'
        self.DIRECT_TEXT = 12  # State for direct message input
        self.msg_request_pattern = 'user_wants_to_send_direct_msg'
        self.msg_req_command = 'the_msg_req_ask'
        self.my_profile_key_starter = 'my_Profile_command_starter'
        self.user_db = UserDatabase()
        self.rel = RelationshipHandler()
        self.rel_db = RelationshipManager()


    def get_profile_create_conversation_handler(self):
        """
        Defines and returns the ConversationHandler for profile creation.
        It specifies entry points, states, and fallbacks for the conversation flow.
        """
        return ConversationHandler(
            entry_points=[CommandHandler(self.create_commend, self.start_profile)],
            states={
                # self.PHOTO: [MessageHandler(filters.PHOTO, self.handle_photo)],
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
        messages = msg(language=context.user_data['lan'])
        context.user_data['user_id'] = update.effective_user.id
        await update.message.reply_text(
            messages.PROFILE_START,
            reply_markup=ReplyKeyboardRemove()  # Removes the custom keyboard
        )
        return self.NAME

    # async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """
    #     Handles the photo input during profile creation. Stores the file_id of the highest
    #     resolution photo and prompts for the user's name.
    #     """
    #     messages = msg(language=context.user_data['lan'])
    #     # Check if a photo was actually sent
    #     if not update.message.photo:
    #         await update.message.reply_text("plz send your photo!")
    #         return self.PHOTO
    #
    #     # Store the file_id of the highest resolution photo
    #     photo_file = await update.message.photo[-1].get_file()
    #     context.user_data['profile_photo'] = photo_file.file_id
    #
    #     await update.message.reply_text(messages.PROFILE_PHOTO_RECEIVED)
    #     return self.NAME

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the name input during profile creation. Stores the name and prompts for age.
        """
        messages = msg(language=context.user_data['lan'])
        context.user_data['name'] = update.message.text

        await update.message.reply_text(messages.PROFILE_ASK_AGE)
        return self.AGE

    async def handle_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the age input during profile creation. Validates age (13-120),
        stores it, and prompts for gender with a custom keyboard.
        """
        messages = msg(language=context.user_data['lan'])
        try:
            age = int(update.message.text)
            if age < 13 or age > 120:
                await update.message.reply_text(
                    messages.PROFILE_INVALID_AGE
                )
                return self.AGE  # Stay in AGE state
            context.user_data['age'] = age
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(
                messages.PROFILE_AGE_NOT_NUMBER
            )
            return self.AGE  # Stay in AGE state

        # Create gender selection keyboard
        reply_keyboard = [["Male"], ["Female"], ["Other"]]
        await update.message.reply_text(
            messages.PROFILE_ASK_GENDER,
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
        messages = msg(language=context.user_data['lan'])
        context.user_data['gender'] = update.message.text

        await update.message.reply_text(
            messages.PROFILE_ASK_ABOUT,
            reply_markup=ReplyKeyboardRemove()  # Removes the custom keyboard
        )
        return self.ABOUT

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the 'about' text input during profile creation. Validates length,
        stores the text, and prompts for location with a "Share Location" button.
        """
        messages = msg(language=context.user_data['lan'])
        if len(update.message.text) > 200:
            await update.message.reply_text(messages.PROFILE_ABOUT_TOO_LONG)
            return self.ABOUT  # Stay in ABOUT state

        context.user_data['about'] = update.message.text

        # Request location with a button that triggers location sharing
        reply_keyboard = [[KeyboardButton("Share Location", request_location=True)]]
        await update.message.reply_text(
            messages.PROFILE_ASK_LOCATION,
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
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)

        # Display the newly created/updated profile
        await self.show_my_profile(update, context)

        return ConversationHandler.END  # End the conversation

    def _self_profile_keyboard(self, user_id):
        messages = msg()
        all_rels = self.rel_db.get_user_relationships(user_id)
        if all_rels:
            num_friends = len(all_rels['friends'])
            num_likes = len(all_rels['liked_by'])
        else:
            num_friends = ""
            num_likes = ""
        return [
            [
                InlineKeyboardButton('Edit', callback_data=f'{self.my_profile_key_starter}: edit'),
                InlineKeyboardButton('Update Photo', callback_data=f'{messages.PROFILE_EDIT_PATTERN}: {messages.PHOTO_PATTERN}')
            ],
            [
                InlineKeyboardButton(f'( {num_likes} ) likes', callback_data=f'{self.rel.rel_inspect_pattern}: {self.rel.like_pattern}'),
                InlineKeyboardButton(f'( {num_friends} ) Friends', callback_data=f"{self.rel.rel_inspect_pattern}: {self.rel.friend_pattern}")
            ]
        ]

    @track_user_interaction
    async def show_my_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays the current user's profile information, including photo, name, age,
        gender, 'about' text, last online status, and a generated user ID.
        Provides inline buttons for editing profile and other actions.
        """
        messages = msg(language=context.user_data['lan'])
        self.load_profile(update, context)  # Ensure user_data is loaded/updated from DB
        user_id = update.effective_user.id

        profile = self.user_db.get_user_information(user_id)  # Retrieve profile from DB

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
        name_display = profile.name if profile.name else "Not set yet"
        age_display = profile.age if profile.age else "Not set yet"
        gender_display = profile.gender if profile.gender else "Not set yet"
        about_display = profile.about if profile.about else "Not set yet"
        online_display = last_online if profile.last_online else "Long time ago"
        generated_id_display = profile.generated_id  # Assuming this is always set if profile exists

        text = messages.PROFILE_DISPLAY.format(
            name=name_display,
            age=age_display,
            gender=gender_display,
            about=about_display,
            last_online=online_display,
            generated_id=generated_id_display
        )




        # Define inline keyboard buttons for profile actions
        keyboard = self._self_profile_keyboard(user_id)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send photo with caption or just text if no photo exists
        if profile.profile_photo:
            await update.message.reply_photo(
                photo=profile.profile_photo,
                caption=text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(text,
                                            reply_markup=reply_markup)




    async def show_my_profile_edit_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Switches the 'My Profile' view to an edit mode, presenting buttons for
        specific profile field edits (Name, About, City, Photo).
        """
        messages = msg(language=context.user_data['lan'])
        self.load_profile(update, context)  # Ensure user data is up-to-date

        # Define inline keyboard buttons for specific edit actions
        keyboard = [
            [
                InlineKeyboardButton('Edit Name', callback_data=f'{messages.PROFILE_EDIT_PATTERN}:{messages.NAME_PATTERN}'),
                InlineKeyboardButton('Edit About', callback_data=f'{messages.PROFILE_EDIT_PATTERN}:{messages.ABOUT_PATTERN}')
                # Mislabeled, should be specific action
            ],
            [
                InlineKeyboardButton('Edit City', callback_data=f'{messages.PROFILE_EDIT_PATTERN}:{messages.CITY_PATTERN}'),
                InlineKeyboardButton('Edit Location', callback_data=f"{messages.PROFILE_EDIT_PATTERN}:{messages.LOCATION_PATTER}")
            ],
            [
                InlineKeyboardButton('Edit Language', callback_data=f'{messages.LANGUAGE_PATTERN}'),

            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query = update.callback_query  # Get the callback query that triggered this

        # Edit the original message's reply markup to show new buttons
        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )

    def _target_profile_keyboard(self, user_id, target_id):
        print(self.rel_db.is_liked(user_id=user_id, target_id=target_id))
        return [
            [
                InlineKeyboardButton('Direct MSG', callback_data=f"{self.msg_request_pattern}: {target_id}"),
                InlineKeyboardButton('Chat Request',
                                     callback_data=f"{self.button_starter_command} chat_request:{target_id}"),
            ],
            [
                InlineKeyboardButton('Like', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.like_pattern}:{target_id}")
                if not self.rel_db.is_liked(user_id=user_id, target_id=target_id) else
                InlineKeyboardButton('Liked <3', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.unlike_pattern}:{target_id}"),


                InlineKeyboardButton('ADD Friend',
                                     callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.friend_pattern}:{target_id}")
                if not self.rel_db.is_friend(user_id=user_id, target_id=target_id) else
                InlineKeyboardButton('Added as Friend', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.unfriend_pattern}:{target_id}")
            ],



            [
                InlineKeyboardButton('block', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.block_pattern}:{target_id}")
                if not self.rel_db.is_block(user_id=user_id, target_id=target_id) else
                InlineKeyboardButton('unblock', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.unblock_pattern}:{target_id}"),

                InlineKeyboardButton('Report', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.report_pattern}:{target_id}")
                if not self.rel_db.is_report(user_id=user_id, target_id=target_id) else
                InlineKeyboardButton('Reported', callback_data=f"{self.rel.rel_starter_pattern}:{self.rel.report_pattern}:{target_id}"),
            ]
        ]
    @track_user_interaction
    async def show_target_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int, is_callback=False):
        """
        Displays the profile information of a target user (not the current user).
        Includes options to send direct messages, chat requests, like, add friend, block, or report.

        Args:
            update (Update): The Telegram Update object.
            context (ContextTypes.DEFAULT_TYPE): The context object for the current update.
            target_id (int): The user ID of the target profile to display.
        """
        self.load_profile(update, context)  # Ensure current user's data is loaded

        profile = self.user_db.get_user_information(target_id)  # Retrieve target user's profile from DB
        user_id = update.effective_user.id

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
        keyboard = self._target_profile_keyboard(user_id, target_id)
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send photo with caption or just text if no photo exists for the target profile
        if is_callback:

            # Handle callback query case
            query = update.callback_query
            await query.answer()

            try:
                if profile.profile_photo:
                    await query.edit_message_media(
                        media=InputMediaPhoto(profile.profile_photo, caption=text),
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(
                        text=text,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                print(f"Error editing message: {e}")
                # Fallback to sending new message if edit fails
                if profile.profile_photo:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=profile.profile_photo,
                        caption=text,
                        reply_markup=reply_markup
                    )
                else:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=text,
                        reply_markup=reply_markup
                    )
        else:
            # Handle regular message case
            if profile.profile_photo:
                await update.message.reply_photo(
                    photo=profile.profile_photo,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup
                )

    def load_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Loads the user's profile data from the database into `context.user_data`.
        Ensures the user exists in the database and updates their `last_online` status.
        """
        # user_id = str(update.effective_chat.id) # Original comment, now using effective_user.id
        self.user_db.add_or_update_user(update.effective_user.id,
                                   context.user_data)  # Ensures user exists and updates last_online
        self.user_db.get_user_data(update.effective_user.id, context.user_data)  # Populates context.user_data



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
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)  # Ensure user record exists
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

    def _language_options_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        language_set = [key for key, value in languages.items()]
        key_set = []
        i = 1
        keys_in_line = []
        for lan in language_set:
            i += 1
            new = InlineKeyboardButton(lan, callback_data=f'set lan: {lan}')
            keys_in_line.append(new)
            if i % 3 == 0 or i == len(language_set):
                key_set.append(keys_in_line)
                keys_in_line = []

        return key_set

    async def language_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = self._language_options_keyboard(update, context)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text='Plz choose your language',
            reply_markup=reply_markup,
        )

    async def buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles callbacks from inline keyboard buttons related to profile interactions
        (e.g., chat requests, direct messages, likes, blocks).
        Routes the actions based on the callback data pattern.
        """
        messages = msg(language=context.user_data['lan'])
        user_id = update.effective_user.id
        message_handler = UserMessage()
        query = update.callback_query

        if query.data.startswith(self.button_starter_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()
            if action == 'chat_request':
                await message_handler.chat_request(update, context, target_id)

        elif query.data.startswith(self.msg_req_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()
            if action == 'accept':
                await self.chat_request_accepted(update, context, int(target_id))
            elif action == 'decline':
                await self.chat_reqeust_declined(update, context, int(target_id))

        elif query.data.startswith(self.my_profile_key_starter):
            action = query.data.split(':')[1].strip().lower()
            if action == 'edit':
                await self.show_my_profile_edit_mode(update, context)

        elif query.data.startswith(messages.LANGUAGE_PATTERN):
            await self.language_options(update, context)

        elif query.data.startswith("set lan"):
            action = query.data.split(':')[1].strip().lower()

            self.user_db.update_len(user_id, action)
            context.user_data['language'] = action
            await query.edit_message_text(
                'language changed'
            )




        elif query.data.startswith(self.rel.rel_starter_pattern):
            action = query.data.split(':')[1].strip().lower()
            target_id = int(query.data.split(':')[2].strip().lower())


            if action == messages.UNLIKE_PATTERN:
                self.rel.unliking_handler(update, context, target_id)
            if action == messages.UNFRIEND_PATTERN:
                self.rel.unadd_friend_handler(update, context, target_id)
            if action == messages.UNBLOCK_PATTERN:
                self.rel.unblock_handler(update, context, target_id)

            try:
                new_keyboard= self._target_profile_keyboard(user_id, target_id)
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(new_keyboard)
                )
            except BadRequest as e:
                print(f'noe changes {e}')



    async def handle_edit_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        messages = msg(language=context.user_data['lan'])
        query = update.callback_query
        action = query.data.split(':')[1].strip().lower()

        await query.answer()

        try:
            if action == messages.NAME_PATTERN:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="Please enter your new name:"
                )
                return self.EDIT_NAME
            elif action == messages.ABOUT_PATTERN:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="Please enter your new bio/about text:"
                )
                return self.EDIT_ABOUT
            elif action == messages.CITY_PATTERN:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="Please enter your new city:"
                )
                return self.EDIT_CITY
            elif action == messages.PHOTO_PATTERN:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="Please send your new profile photo:",

                )
                return self.EDIT_PHOTO
            elif action == messages.LOCATION_PATTER:

                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text='Please send your location',


                )

                return self.EDIT_LOCATION
        except Exception as e:
            print(f"Error handling edit button: {e}")
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="Something went wrong. Please try again."
            )
            return ConversationHandler.END

    async def handle_edit_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Reuse your existing name validation logic
        new_name = update.message.text


        # Update in database
        context.user_data['name'] = new_name
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)
        await update.message.reply_text(f"Name updated to: {new_name}")
        await self.show_my_profile(update, context)
        return ConversationHandler.END

    async def handle_edit_about_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Reuse your existing about validation logic
        new_about = update.message.text
        if len(new_about) > 200:  # Reuse your length check
            await update.message.reply_text("Bio is too long, please shorten it")
            return self.EDIT_ABOUT

        # Update in database
        context.user_data['about'] = new_about
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)
        await update.message.reply_text("Bio updated successfully!")
        await self.show_my_profile(update, context)
        return ConversationHandler.END

    async def handle_edit_city_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_city = update.message.text
        # Add any city validation if needed

        # Update in database - adjust field name if you use 'location' instead
        context.user_data['city'] = new_city
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)
        await update.message.reply_text(f"City updated to: {new_city}")
        await self.show_my_profile(update, context)
        return ConversationHandler.END

    async def handle_edit_location_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        location = update.message.location
        context.user_data['location'] = (location.latitude, location.longitude)
        context.user_data['latitude'] = context.user_data['location'][0]
        context.user_data['longitude'] = context.user_data['location'][1]
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)
        await update.message.reply_text(f"City updated to: new location")
        await self.show_my_profile(update, context)
        return ConversationHandler.END

    async def handle_edit_photo_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.photo:
            await update.message.reply_text("Please send a valid photo")
            return self.EDIT_PHOTO

        # Get highest resolution photo
        photo_file = await update.message.photo[-1].get_file()
        photo_id = photo_file.file_id

        # Update in database
        context.user_data['profile_photo'] = photo_id
        self.user_db.add_or_update_user(update.effective_user.id, context.user_data)
        await update.message.reply_text("Profile photo updated!")
        await self.show_my_profile(update, context)
        return ConversationHandler.END

    async def cancel_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Profile editing cancelled')
        return ConversationHandler.END

    def get_profile_edit_conversation_handler(self):
        messages = msg()
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(
                self.handle_edit_button_click,
                pattern=f'^{messages.PROFILE_EDIT_PATTERN}'
            )],
            states={
                self.EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_name_input)],
                self.EDIT_ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_about_input)],
                self.EDIT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_city_input)],
                self.EDIT_PHOTO: [MessageHandler(filters.PHOTO, self.handle_edit_photo_input)],
                self.EDIT_LOCATION: [MessageHandler(filters.LOCATION, self.handle_edit_location_input)],


            },
            fallbacks=[CommandHandler('cancel', self.cancel_edit)],
            allow_reentry=True
        )
    @track_user_interaction
    async def start_msg_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Initiates the direct message request conversation.
        Stores the target user's ID and prompts the user to send their message.
        """
        messages = msg(language=context.user_data['lan'])
        query = update.callback_query
        user_id = update.effective_user.id
        target_id = query.data.split(':')[1].strip()  # Extract target_id from callback data
        if self.rel_db.is_block(target_id, user_id):
            await context.bot.send_message(user_id,
                                           text=messages.BLOCKED_FROM_USER_WARNING)
            return
        context.user_data['request_from_id'] = target_id  # Store target ID in user_data
        context.user_data['user_id'] = update.effective_user.id  # Ensure current user_id is in context

        await context.bot.send_message(user_id, text=messages.DIRECT_MSG_PROMPT)
        return self.DIRECT_TEXT  # Move to the state for direct message text input

    async def handle_direct_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the text input for a direct message request.
        Validates message length, adds it as a 'requested' message to the database,
        and notifies both sender and receiver.
        """
        messages = msg(language=context.user_data['lan'])
        user_id = update.effective_user.id
        target_id = context.user_data['request_from_id']  # Retrieve target ID
        the_msg = update.message.text

        # Basic message validation
        if not the_msg:
            return ConversationHandler.END  # End conversation if no message text
        if len(the_msg) > 250:
            # Maybe send a warning message and stay in the state
            await update.message.reply_text(messages.DIRECT_MSG_TOO_LONG)
            return self.DIRECT_TEXT

        chat_db = ChatDatabase()  # Instance of ChatDatabase

        # Attempt to add the message as a requested message in the database
        if chat_db.add_requested_msg(user_id, target_id, the_msg):
            # Create inline keyboard for recipient to accept or decline the message request
            keyboard = [
                [
                    InlineKeyboardButton("Accept", callback_data=f"{self.msg_req_command}: accept: {user_id}"),
                    InlineKeyboardButton("Decline", callback_data=f"{self.msg_req_command}: decline: {user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Notify the sender that their request has been sent
            await update.message.reply_text(messages.DIRECT_MSG_SENT)
            # Notify the recipient with the message request and action buttons
            await context.bot.send_message(target_id,
                                           text=messages.DIRECT_MSG_REQUEST.format(user_id=user_id),
                                           reply_markup=reply_markup)
            return ConversationHandler.END  # End conversation
        else:
            # Handle case where message could not be added (e.g., DB error)
            await update.message.reply_text(messages.DIRECT_MSG_ERROR)
            return ConversationHandler.END
    @track_user_interaction
    async def chat_request_accepted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        """
        Handles the acceptance of a chat request. Retrieves and sends the requested messages
        from the sender to the accepting user, and notifies the sender.

        Args:
            update (Update): The Telegram Update object (contains callback_query).
            context (ContextTypes.DEFAULT_TYPE): The context object.
            target_id (int): The user ID of the sender whose messages are being accepted.
        """
        messages = msg(language=context.user_data['lan'])
        user_id = update.effective_user.id
        message_db = ChatDatabase()

        # Get requested messages from the database
        msgs = message_db.get_msg_requests_from_map(user_id, target_id)
        query = update.callback_query  # The callback query that triggered this action

        if msgs:
            await query.edit_message_text(messages.DIRECT_MSG_ACCEPTED.format(target_id=target_id))  # Edit original button message
            for the_msg in msgs:
                await context.bot.send_message(user_id,
                                               text=f"/chaT_{target_id}: {the_msg}")  # Send each message to the accepting user
            await context.bot.send_message(target_id, text=messages.DIRECT_MSG_RECEIVED.format(user_id=user_id))  # Notify sender
        else:
            await query.edit_message_text(messages.DIRECT_MSG_NO_MSGS.format(target_id=target_id))  # No messages found

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
        messages = msg(language=context.user_data['lan'])
        user_id = update.effective_user.id
        message_db = ChatDatabase()
        query = update.callback_query  # The callback query that triggered this action

        # Attempt to clear requested messages from the database
        if message_db.clear_msg_requests_from_map(user_id, target_id):
            await query.edit_message_text(messages.DIRECT_MSG_DECLINED.format(target_id=target_id))  # Edit original button message
            await context.bot.send_message(target_id,
                                           text=messages.DIRECT_MSG_DECLINE_NOTIFY.format(user_id=user_id))  # Notify sender
        else:
            await query.edit_message_text(messages.DIRECT_MSG_FAILED_DECLINE.format(target_id=target_id))  # Error or no messages

    @track_user_interaction
    async def show_profile_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles requests to show a user's profile based on a '/chaT_<generated_id>' command.
        Validates the generated ID and then calls the profile handler to display the profile.
        """
        messages = msg(language=context.user_data['lan'])
        user_id = update.effective_user.id
        target_id_parts = update.message.text.split('_', 1)
        if self.user_db.get_user_generated_id(user_id) == target_id_parts[1]:
            await self.show_my_profile(update, context)
            return

        if len(target_id_parts) < 2:
            await update.message.reply_text(messages.INVALID_FORMAT.format(command="chaT"))
            return

        command, target_id_generated = target_id_parts
        if not target_id_generated:
            await update.message.reply_text(messages.INVALID_ITEM)
            return

        if not self.user_db.get_user_id_from_generated_id(target_id_generated):
            await update.message.reply_text(messages.USER_NOT_REGISTERED)
            return

        target_id = self.user_db.get_user_id_from_generated_id(target_id_generated)
        await self.show_target_profile(update, context, target_id)

    def show_profile_handler(self):
        messages = msg()
        return MessageHandler(filters.Regex(messages.CHAT_PROFILE_REGEX), self.show_profile_request)


    def get_all_handlers(self) -> list:
        """
        Returns a list of all ConversationHandlers managed by the Profile class.
        This is used to register them with the Telegram bot application.
        """
        return [
            self.get_profile_create_conversation_handler(),
            self.direct_msg_conversation_handler(),
            self.show_profile_handler(),
            CommandHandler("profile", self.show_my_profile),
            self.get_profile_edit_conversation_handler()
        ]
