from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.handlers.intraction import track_user_interaction
from bot.handlers.telegram_conversations import TorobConversation
from bot.db.database import TorobDb
from bot.utils.messages_manager import messages as msg
from bot.utils.messages_manager import languages as the_lans

# messages = msg(language=context.user_data['lan'])

class TorobInteract:
    def __init__(self):
        self.torob_conversation = TorobConversation()
        self.torob_db = TorobDb()


    @track_user_interaction
    async def torob(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Initiates the Torob price tracking feature.
        Provides options to check existing items or add new ones.
        """
        messages = msg(language=context.user_data['lan'])

        keyboard = [
            [InlineKeyboardButton(messages.CHECK_ITEMS_BUTTON, callback_data='torob: check')],
            [InlineKeyboardButton(messages.ADD_NEW_ITEMS_BUTTON, callback_data=self.torob_conversation.query_add_pattern)],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Torob Scraper: ",
            reply_markup=reply_markup
        )

    @track_user_interaction
    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the '/item_<item_id>' command to enter item editing mode for Torob items.
        Allows users to edit price, URL, name, or delete an item.
        """
        messages = msg(language=context.user_data['lan'])
        user_id = update.effective_user.id
        item_id_parts = update.message.text.split('_', 1)

        if len(item_id_parts) < 2:
            await update.message.reply_text(messages.INVALID_FORMAT.format(command="item"))
            return

        try:
            command, item_id = item_id_parts
            item_data = self.torob_db.get_item_by_id(int(item_id))
        except ValueError:
            await update.message.reply_text(messages.INVALID_FORMAT.format(command="item"))
            return

        if not item_data:
            await update.message.reply_text(messages.INVALID_ITEM)
            return

        if not self.torob_db.check_ownership(user_id, int(item_id)):
            await update.message.reply_text(messages.NOT_OWNER)
            return

        context.user_data['editing_item_id'] = int(item_id)
        keyboard = [
            [
                InlineKeyboardButton(messages.TOROB_EDIT_PRICE, callback_data=f'{self.torob_conversation.edit_price_pattern}'),
                InlineKeyboardButton(messages.TOROB_EDIT_URL, callback_data=f'{self.torob_conversation.edit_url_pattern}'),
                InlineKeyboardButton(messages.TOROB_EDIT_NAME, callback_data=f'{self.torob_conversation.edit_name_pattern}')
            ],
            [InlineKeyboardButton(messages.TOROB_EDIT_DELETE, callback_data=f'{self.torob_conversation.delete_item_pattern}')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            user_id,
            text=messages.ITEM_ON_EDIT_MODE.format(
                name=item_data.name_of_item,
                price=item_data.user_preferred_price,
                url=item_data.torob_url
            ),
            reply_markup=reply_markup
        )

    async def check_torob_list(self, query, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays a list of Torob items tracked by the user, including their latest prices and check times.
        Provides options to add new items or edit existing ones.
        """

        messages = msg(language=context.user_data['lan'])
        user_id = query.from_user.id
        user_items = self.torob_db.get_user_items(user_id)
        final_note = ""
        keyboard = [
            [InlineKeyboardButton(messages.ADD_ITEM_BUTTON, callback_data=self.torob_conversation.query_add_pattern)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if user_items:

            for item in user_items:
                name = item.name_of_item
                latest_price = self.torob_db.get_latest_price(item.item_id)
                signal_price = messages.PRICE_OK_ICON if latest_price and latest_price <= item.user_preferred_price else messages.PRICE_HIGH_ICON
                latest_check = self.torob_db.get_latest_check(item.item_id)
                item_id = item.item_id

                if latest_check and latest_price:
                    item_note = messages.ITEM_CHECKED_FORMAT.format(
                        signal=signal_price,
                        name=name,
                        latest_check=latest_check.strftime("%Y/%m/%d: %H"),
                        latest_price=latest_price,
                        item_id=item_id,
                        divider=messages.DIVIDER
                    )
                else:
                    item_note = messages.ITEM_UNCHECKED_FORMAT.format(
                        signal=signal_price,
                        name=name,
                        item_id=item_id,
                        divider=messages.DIVIDER
                    )
                final_note += item_note

        if final_note:
            await query.edit_message_text(
                text=final_note,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=messages.NOTHING_TO_SHOW,
                reply_markup=reply_markup
            )


    async def button(self, update, context):

        query = update.callback_query
        await query.answer()

        if query.data.startswith('torob:'):

            action = query.data.split(':')[1].strip().lower()
            if action == "check":
                await self.check_torob_list(query, context)

    #here add handlers for languages
    def handlers(self):
        languages = [key for key, value in the_lans.items()]
        handlers = []
        for lan in languages:
            messages = msg(language=lan)
            lan_handlers = [
                MessageHandler(filters.Regex(fr"^{messages.TOROB_BUTTON}$"), self.torob),
                MessageHandler(filters.Regex(messages.ITEM_EDIT_REGEX), self.edit_command)
            ]
            handlers += lan_handlers


        return handlers