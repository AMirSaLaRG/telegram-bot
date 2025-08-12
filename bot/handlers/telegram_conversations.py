from datetime import datetime
from datetime import timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    filters,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from bot.db.database import UserDatabase, TorobDb, ChatDatabase
from urllib.parse import urlparse
from bot.handlers.telegram_chat_handler import UserMessage

# Initialize DB instances
user_db = UserDatabase()
from bot.utils.messages_manager import messages as msg

# messages = msg(language=context.user_data['lan'])

from bot.handlers.intraction import track_user_interaction
from bot.handlers.start import Start


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
        self.calculate_command = "calculator"

    def get_calculated_price_conversation_handler(self):
        """
        Defines and returns the ConversationHandler for the price calculation feature.
        It specifies entry points, states, and fallbacks for the conversation flow.
        """
        return ConversationHandler(
            entry_points=[
                CommandHandler(self.calculate_command, self.start_calculation),
                CallbackQueryHandler(
                    self.start_calculation, pattern=f"^{self.calculate_command}$"
                ),
            ],
            states={
                self.ITEM: [CallbackQueryHandler(self.handle_item)],
                self.AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_amount)
                ],
                self.CONST_FEE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_const_fee
                    )
                ],
                self.SHOP_FEE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_shop_fee
                    )
                ],
                self.TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Cancels the current calculation conversation and sends a cancellation message.
        """
        messages = msg(language=context.user_data["lan"])
        # Checks if update is a message or a callback query to reply appropriately
        if update.message:
            await update.message.reply_text(messages.CALCULATOR_STOPPED)
        elif update.callback_query:
            await (
                update.callback_query.answer()
            )  # Answer the callback query to remove loading indicator
            await update.callback_query.edit_message_text(
                messages.CALCULATOR_STOPPED
            )  # Edit message to confirm cancellation
        await Start().start(update, context)
        return ConversationHandler.END

    async def start_calculation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Starts the price calculation conversation. Presents initial item options.
        """
        messages = msg(language=context.user_data["lan"])
        # Handle both Message (command) and CallbackQuery (button) updates
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message

        # Define inline keyboard with item options
        keyboard = [[InlineKeyboardButton("gold: 18karat", callback_data="18kr")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        cancel_keyboard = [[KeyboardButton("/cancel")]]
        cancel_reply = ReplyKeyboardMarkup(cancel_keyboard, resize_keyboard=True)
        # Send message with item options
        await context.bot.send_message(
            text="-", chat_id=message.chat.id, reply_markup=cancel_reply
        )
        await context.bot.send_message(
            chat_id=message.chat.id,
            text=messages.CALCULATOR_START,
            reply_markup=reply_markup,
        )

        return self.ITEM  # Move to the ITEM state

    async def handle_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the selected item for calculation. Validates the item and
        prompts for the amount.
        """
        messages = msg(language=context.user_data["lan"])
        query = update.callback_query
        await query.answer()  # Answer the callback query to remove loading indicator
        item = query.data

        # Validate selected item
        if not item == "18kr":
            await query.edit_message_text(messages.CALCULATOR_INVALID_ITEM)
            return self.ITEM  # Stay in ITEM state

        context.user_data["calculate_item"] = item  # Store selected item

        await query.edit_message_text(messages.CALCULATOR_ASK_AMOUNT.format(item=item))
        return self.AMOUNT  # Move to the AMOUNT state

    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the amount input for the selected item. Validates if it's a number
        and prompts for the construction fee percentage.
        """
        messages = msg(language=context.user_data["lan"])
        try:
            float(
                update.message.text
            )  # Attempt to convert input to float for validation
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(
                f"Plz enter the amount of {context.user_data['calculate_item']}\n gold: gram\nonly numbers"
            )
            return self.AMOUNT  # Stay in AMOUNT state
        else:
            context.user_data["amount"] = (
                update.message.text
            )  # Store amount as text (can be converted to float later)

            await update.message.reply_text(messages.CALCULATOR_ASK_CONSTRUCTION_FEE)
            return self.CONST_FEE  # Move to the CONST_FEE state

    async def handle_const_fee(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the construction fee percentage input. Validates the percentage (1-100)
        and prompts for the shop fee percentage.
        """
        messages = msg(language=context.user_data["lan"])
        try:
            const_fee = float(update.message.text)  # Attempt to convert input to float
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(
                "Plz send contraction fee percentage: (1 to 100)"
            )
            return self.CONST_FEE  # Stay in CONST_FEE state
        else:
            if not 1 <= int(const_fee) <= 100:  # Check if percentage is within range
                await update.message.reply_text(
                    "Plz send contraction fee percentage: (1 to 100)"
                )
                return self.CONST_FEE  # Stay in CONST_FEE state
            context.user_data["const_fee"] = update.message.text  # Store as text

            await update.message.reply_text(messages.CALCULATOR_ASK_SHOP_FEE)
            return self.SHOP_FEE  # Move to the SHOP_FEE state

    async def handle_shop_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the shop fee percentage input. Validates the percentage (1-100)
        and prompts for the text percentage.
        """
        messages = msg(language=context.user_data["lan"])
        try:
            shop_fee = float(update.message.text)  # Attempt to convert input to float
        except ValueError:  # If input is not a valid number
            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE  # Stay in SHOP_FEE state
        else:
            if not 1 <= int(shop_fee) <= 100:  # Check if percentage is within range
                await update.message.reply_text(
                    "Plz send shop fee percentage: (1 to 100)"
                )
                return self.CONST_FEE  # Should be SHOP_FEE (typo in original code), staying in current state
            context.user_data["shop_fee"] = update.message.text  # Store as text

            await update.message.reply_text(messages.CALCULATOR_ASK_TEXT_FEE)
            return self.TEXT  # Move to the TEXT state

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the text percentage input. Validates the percentage (1-100)
        and then displays the calculated result.
        """
        messages = msg(language=context.user_data["lan"])
        try:
            text_fee = float(update.message.text)  # Corrected variable name for clarity
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(messages.CALCULATOR_ASK_TEXT_FEE)
            return self.TEXT  # Stay in TEXT state
        else:
            if not 1 <= int(text_fee) <= 100:  # Check if percentage is within range
                await update.message.reply_text(messages.CALCULATOR_ASK_TEXT_FEE)
                return self.TEXT  # Stay in TEXT state
            context.user_data["text"] = update.message.text  # Store as text

            await self.show_calculated_result(update, context)  # Display results

            return ConversationHandler.END  # End the conversation

    async def show_calculated_result(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Displays the summary of the calculated price based on user inputs.
        """
        messages = msg(language=context.user_data["lan"])
        # Construct the result text from stored user data
        display_item = context.user_data["calculate_item"]
        display_amount = context.user_data["amount"]
        display_const_fee = context.user_data["const_fee"]
        display_shop_fee = context.user_data["shop_fee"]
        display_text_fee = context.user_data["text"]

        text = messages.CALCULATOR_RESULT.format(
            item=display_item,
            amount=display_amount,
            const_fee=display_const_fee,
            shop_fee=display_shop_fee,
            text_fee=display_text_fee,
        )

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
        self.query_add_pattern = "add_new_torob_item"
        self.edit_price_pattern = "torob_edit_price"
        self.edit_url_pattern = "torob_edit_url"
        self.edit_name_pattern = "torob_edit_name"
        self.delete_item_pattern = "torob_delete_item"
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
                CallbackQueryHandler(
                    self.start_add, pattern=f"^{self.query_add_pattern}$"
                )
            ],
            states={
                self.NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name)
                ],
                self.PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_price)
                ],
                self.URL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def torob_edit_price_handler(self):
        """
        Defines and returns the ConversationHandler for editing a Torob item's price.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.start_edit_price, pattern=f"^{self.edit_price_pattern}$"
                )
            ],
            states={
                self.EDIT_PRICE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_edit_price
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def torob_edit_url_handler(self):
        """
        Defines and returns the ConversationHandler for editing a Torob item's URL.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.start_edit_url, pattern=f"^{self.edit_url_pattern}$"
                )
            ],
            states={
                self.EDIT_URL: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_edit_url
                    )
                ],
                # self.URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)], # This line seems like a duplicate state entry or a leftover
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def torob_edit_name_handler(self):
        """
        Defines and returns the ConversationHandler for editing a Torob item's name.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.start_edit_name, pattern=f"^{self.edit_name_pattern}$"
                )
            ],
            states={
                self.EDIT_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_edit_name
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    def torob_delete_item(self):
        """
        Defines and returns the ConversationHandler for deleting a Torob item.
        """
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.start_delete_item, pattern=f"^{self.delete_item_pattern}$"
                )
            ],
            states={
                self.DELETE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_delete_item
                    )
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Cancels the current Torob conversation (add/edit/delete) and sends a cancellation message.
        """
        messages = msg(language=context.user_data["lan"])
        if update.callback_query:
            await update.callback_query.answer()  # Acknowledge the callback query
            await update.callback_query.edit_message_text(messages.OPERATION_CANCELLED)
        elif update.message:
            await update.message.reply_text(messages.OPERATION_CANCELLED)
        await Start().start(update, context)
        return ConversationHandler.END  # End the conversation

    async def _send_fallback_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
    ):
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
            elif (
                "chat_id" in context.user_data
            ):  # Fallback if neither callback_query nor message exists
                await context.bot.send_message(
                    chat_id=context.user_data["chat_id"], text=text
                )
        except Exception as e:
            print(f"⚠️ Failed to send fallback message: {e}")

    @track_user_interaction
    async def start_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation to add a new Torob item. Prompts for the item's name.
        """
        messages = msg(language=context.user_data["lan"])
        if not update.callback_query:  # Ensure it's triggered by a callback query
            return ConversationHandler.END
        await update.callback_query.answer()  # Acknowledge the callback query
        keyboard = [[KeyboardButton("/cancel")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="-", reply_markup=reply_markup
        )
        await update.callback_query.edit_message_text(
            messages.TOROB_ADD_START,
        )
        return self.NAME  # Move to the NAME state

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the item name input during the add item conversation.
        Validates length and prompts for the preferred price.
        """
        messages = msg(language=context.user_data["lan"])
        if not update.message or not update.message.text:
            await self._send_fallback_message(
                update, context, messages.TEXT_INPUT_REQUIRED
            )
            return self.NAME  # Stay in NAME state

        if len(update.message.text) > 150:  # Validate name length
            await update.message.reply_text(messages.TOROB_INVALID_NAME_LENGTH)
            return self.NAME  # Stay in NAME state

        self.name = update.message.text  # Store the name temporarily
        await update.message.reply_text(messages.TOROB_ASK_PRICE.format(name=self.name))
        return self.PRICE  # Move to the PRICE state

    async def handle_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the preferred price input during the add item conversation.
        Validates if it's a positive number and prompts for the Torob URL.
        """
        messages = msg(language=context.user_data["lan"])
        try:
            price = float(update.message.text)
            if price <= 0:  # Price must be positive
                await update.message.reply_text(messages.TOROB_PRICE_TOO_LOW)
                return self.PRICE  # Stay in PRICE state
            self.price = price  # Store the price temporarily
        except ValueError:  # If input is not a valid number
            await update.message.reply_text(messages.TOROB_INVALID_PRICE)
            return self.PRICE  # Stay in PRICE state
        else:  # If price is valid
            await update.message.reply_text(
                messages.TOROB_ASK_URL.format(name=self.name)
            )
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
                return "torob.com" in result.netloc
            return False
        except Exception as e:  # Catch any parsing errors
            print(f"torob conversation: {e}")
            return False

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the Torob URL input during the add item conversation.
        Validates the URL, adds the item to the database, and ends the conversation.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        the_url = update.message.text

        if not self.is_torob_url(the_url):  # Validate if it's a valid Torob URL
            await update.message.reply_text(messages.TOROB_INVALID_URL)
            return self.URL  # Stay in URL state

        self.url = the_url  # Store the URL temporarily

        # Attempt to add the item to the database
        if self.db.add_item(user_id, self.price, self.url, self.name):
            await update.message.reply_text(
                messages.TOROB_ADD_SUCCESS.format(name=self.name, price=self.price)
            )
            # Clear temporary stored data
            self.price = None
            self.url = None
            self.name = None
            await Start().start(update, context)
            return ConversationHandler.END  # End the conversation
        else:  # If item could not be added (e.g., DB error)
            self.url = None  # Clear URL, might be invalid
            await update.message.reply_text(messages.TOROB_ADD_FAILED)
            return self.URL  # Stay in URL state

    @track_user_interaction
    async def start_delete_item(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Starts the conversation for deleting a Torob item.
        Confirms user ownership and prompts for confirmation.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get(
            "editing_item_id", ""
        )  # Get item ID from user_data
        user_id = update.effective_user.id

        if not update.callback_query:  # Ensure triggered by callback
            return ConversationHandler.END

        # Check if the user owns this item
        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(messages.TOROB_NOT_OWNER)
            return ConversationHandler.END  # End if not owner

        await update.callback_query.answer()  # Acknowledge callback
        await update.callback_query.edit_message_text(messages.TOROB_DELETE_PROMPT)
        return self.DELETE  # Move to the DELETE state for confirmation

    async def handle_delete_item(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the confirmation for deleting a Torob item. Deletes the item from DB
        and shows updated item options.
        """
        item_id = context.user_data.get("editing_item_id", "")
        self.db.delete_item(item_id)  # Delete the item from the database
        await self.show_item_edit_options(
            update, context
        )  # Show updated options (will indicate deletion)
        return ConversationHandler.END  # End the conversation

    @track_user_interaction
    async def start_edit_price(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Starts the conversation for editing a Torob item's preferred price.
        Confirms user ownership and prompts for the new price.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get("editing_item_id", "")
        user_id = update.effective_user.id

        keyboard = [[KeyboardButton("/cancel")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        if not update.callback_query:
            return ConversationHandler.END

        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(messages.TOROB_NOT_OWNER)
            return ConversationHandler.END

        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Editing", reply_markup=reply_markup
        )
        await update.callback_query.edit_message_text(
            messages.TOROB_ASK_NEW_PRICE,
        )
        return self.EDIT_PRICE  # Move to the EDIT_PRICE state

    async def handle_edit_price(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the new price input for editing a Torob item.
        Validates the price, updates it in the DB, and shows updated item options.
        """
        item_id = context.user_data.get("editing_item_id", "")
        try:
            price = float(update.message.text)  # Convert input to float
        except ValueError:  # If input is not a valid number
            await update.message.reply_text("Please enter price in numbers")
            return self.EDIT_PRICE  # Stay in EDIT_PRICE state
        else:
            self.db.update_preferred_price(item_id, price)  # Update price in DB
            await self.show_item_edit_options(update, context)  # Show updated options
            return ConversationHandler.END  # End the conversation

    @track_user_interaction
    async def start_edit_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation for editing a Torob item's URL.
        Confirms user ownership and prompts for the new URL.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get("editing_item_id", "")
        user_id = update.effective_user.id

        keyboard = [[KeyboardButton("/cancel")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        if not update.callback_query:
            return ConversationHandler.END

        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(messages.TOROB_NOT_OWNER)
            return ConversationHandler.END

        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Editing", reply_markup=reply_markup
        )
        await update.callback_query.edit_message_text(messages.TOROB_ASK_NEW_URL)
        return self.EDIT_URL  # Move to the EDIT_URL state

    async def handle_edit_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the new URL input for editing a Torob item.
        Validates the URL, updates it in the DB, and shows updated item options.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get("editing_item_id", "")
        user_id = (
            update.effective_user.id
        )  # user_id is not used here, but was in original for check_ownership
        the_url = update.message.text

        if not self.is_torob_url(the_url):  # Validate if it's a valid Torob URL
            await update.message.reply_text("Please send a torob url ")
            return self.EDIT_URL  # Stay in EDIT_URL state

        if self.db.update_url(item_id, the_url):  # Update URL in DB
            await self.show_item_edit_options(update, context)  # Show updated options
            return ConversationHandler.END  # End the conversation
        else:  # If update failed
            await update.message.reply_text(messages.TOROB_URL_UPDATE_FAILED)
            return self.EDIT_URL  # Stay in EDIT_URL state

    @track_user_interaction
    async def start_edit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the conversation for editing a Torob item's name.
        Confirms user ownership and prompts for the new name.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get("editing_item_id", "")
        user_id = update.effective_user.id

        keyboard = [[KeyboardButton("/cancel")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        if not update.callback_query:
            return ConversationHandler.END

        if not self.db.check_ownership(user_id, item_id):
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(messages.TOROB_NOT_OWNER)
            return ConversationHandler.END

        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_user.id, text="Editing", reply_markup=reply_markup
        )
        await update.callback_query.edit_message_text(messages.TOROB_ASK_NEW_NAME)
        return self.EDIT_NAME  # Move to the EDIT_NAME state

    async def handle_edit_name(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the new name input for editing a Torob item.
        Validates length, updates it in the DB, and shows updated item options.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get("editing_item_id", "")

        if not update.message or not update.message.text:
            await self._send_fallback_message(
                update, context, messages.TEXT_INPUT_REQUIRED
            )
            return self.EDIT_NAME  # Stay in EDIT_NAME state

        if len(update.message.text) > 150:  # Validate name length
            await update.message.reply_text(
                "Please enter a string with less than 150 characters!"
            )
            return self.EDIT_NAME  # Stay in EDIT_NAME state

        if self.db.update_name(item_id, update.message.text):  # Update name in DB
            await self.show_item_edit_options(update, context)  # Show updated options
            return ConversationHandler.END  # End the conversation
        else:
            await update.message.reply_text(messages.TOROB_NAME_UPDATE_FAILED)
            return self.EDIT_NAME  # Stay in EDIT_NAME state

    @track_user_interaction
    async def show_item_edit_options(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Displays the current details of an item after an edit operation (or deletion),
        along with inline buttons for further editing or deletion.
        """
        messages = msg(language=context.user_data["lan"])
        item_id = context.user_data.get("editing_item_id", "")
        item_data = self.db.get_item_by_id(item_id)  # Retrieve the item data

        if item_data:  # If the item still exists (i.e., not just deleted)
            # Define inline keyboard with edit/delete options
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Edit Price", callback_data=f"{self.edit_price_pattern}"
                    ),
                    InlineKeyboardButton(
                        "Edit URL", callback_data=f"{self.edit_url_pattern}"
                    ),
                    InlineKeyboardButton(
                        "Edit Name", callback_data=f"{self.edit_name_pattern}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Delete", callback_data=f"{self.delete_item_pattern}"
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Check if the update is from a message or callback_query to reply appropriately
            if hasattr(update, "message"):
                name = item_data.name_of_item
                price = item_data.user_preferred_price
                url = item_data.torob_url
                await update.message.reply_text(
                    messages.TOROB_UPDATE_SUCCESS.format(
                        name=name, price=price, url=url
                    ),
                    reply_markup=reply_markup,
                )
            else:  # Assuming it's a callback query
                name = item_data.name_of_item
                price = item_data.user_preferred_price
                url = item_data.torob_url
                await update.callback_query.edit_message_text(
                    messages.TOROB_UPDATE_SUCCESS.format(
                        name=name, price=price, url=url
                    ),
                    reply_markup=reply_markup,
                )
        else:  # If the item no longer exists (presumably deleted)
            if hasattr(update, "message"):
                await update.message.reply_text(
                    messages.TOROB_DELETE_SUCCESS
                )  # Notify deletion and suggest /start

            else:  # Assuming it's a callback query
                await update.callback_query.edit_message_text(
                    messages.TOROB_DELETE_SUCCESS
                )  # Notify deletion and suggest /start

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
