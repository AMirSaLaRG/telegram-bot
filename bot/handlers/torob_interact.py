from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.handlers.intraction import track_user_interaction
from bot.utils.messages import Messages
from bot.handlers.telegram_conversations import TorobConversation
from bot.db.database import TorobDb


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

        keyboard = [
            [InlineKeyboardButton(Messages.CHECK_ITEMS_BUTTON, callback_data='torob: check')],
            [InlineKeyboardButton(Messages.ADD_NEW_ITEMS_BUTTON, callback_data=self.torob_conversation.query_add_pattern)],
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
        user_id = update.effective_user.id
        item_id_parts = update.message.text.split('_', 1)

        if len(item_id_parts) < 2:
            await update.message.reply_text(Messages.INVALID_FORMAT.format(command="item"))
            return

        try:
            command, item_id = item_id_parts
            item_data = self.torob_db.get_item_by_id(int(item_id))
        except ValueError:
            await update.message.reply_text(Messages.INVALID_FORMAT.format(command="item"))
            return

        if not item_data:
            await update.message.reply_text(Messages.INVALID_ITEM)
            return

        if not self.torob_db.check_ownership(user_id, int(item_id)):
            await update.message.reply_text(Messages.NOT_OWNER)
            return

        context.user_data['editing_item_id'] = int(item_id)
        keyboard = [
            [
                InlineKeyboardButton('Edit Price', callback_data=f'{self.torob_conversation.edit_price_pattern}'),
                InlineKeyboardButton('Edit URL', callback_data=f'{self.torob_conversation.edit_url_pattern}'),
                InlineKeyboardButton('Edit Name', callback_data=f'{self.torob_conversation.edit_name_pattern}')
            ],
            [InlineKeyboardButton('delete', callback_data=f'{self.torob_conversation.delete_item_pattern}')],
            [InlineKeyboardButton('home', callback_data='item_edit:home')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            user_id,
            text=Messages.ITEM_ON_EDIT_MODE.format(
                name=item_data.name_of_item,
                price=item_data.user_preferred_price,
                url=item_data.torob_url
            ),
            reply_markup=reply_markup
        )
    @track_user_interaction
    async def check_torob_list(self, query, context: ContextTypes.DEFAULT_TYPE):
        """
        Displays a list of Torob items tracked by the user, including their latest prices and check times.
        Provides options to add new items or edit existing ones.
        """
        user_id = query.from_user.id
        user_items = self.torob_db.get_user_items(user_id)
        final_note = ""
        keyboard = [
            [InlineKeyboardButton(Messages.ADD_ITEM_BUTTON, callback_data=self.torob_conversation.query_add_pattern)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if user_items:
            for item in user_items:
                name = item.name_of_item
                latest_price = self.torob_db.get_latest_price(item.item_id)
                signal_price = Messages.PRICE_OK_ICON if latest_price and latest_price <= item.user_preferred_price else Messages.PRICE_HIGH_ICON
                latest_check = self.torob_db.get_latest_check(item.item_id)
                item_id = item.item_id

                if latest_check and latest_price:
                    item_note = Messages.ITEM_CHECKED_FORMAT.format(
                        signal=signal_price,
                        name=name,
                        latest_check=latest_check.strftime("%Y/%m/%d: %H"),
                        latest_price=latest_price,
                        item_id=item_id,
                        divider=Messages.DIVIDER
                    )
                else:
                    item_note = Messages.ITEM_UNCHECKED_FORMAT.format(
                        signal=signal_price,
                        name=name,
                        item_id=item_id,
                        divider=Messages.DIVIDER
                    )
                final_note += item_note

        if final_note:
            await query.edit_message_text(
                text=final_note,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=Messages.NOTHING_TO_SHOW,
                reply_markup=reply_markup
            )

    @track_user_interaction
    async def button(self, update, context):

        query = update.callback_query
        await query.answer()

        if query.data.startswith('torob:'):
            action = query.data.split(':')[1].strip().lower()
            if action == "check":
                await self.check_torob_list(query, context)

    def handlers(self):
        return [
            MessageHandler(filters.Regex(Messages.TOROB_REGEX), self.torob),
            MessageHandler(filters.Regex(Messages.ITEM_EDIT_REGEX), self.edit_command)
        ]