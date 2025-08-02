from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
import logging

from bot.handlers.telegram_conversations import Calculator
from bot.db.database import GoldPriceDatabase
from bot.handlers.intraction import track_user_interaction
from bot.utils.messages import Messages




class GoldDollarReport:
    def __init__(self):
        self.gold_db = GoldPriceDatabase()
        self.calculator = Calculator()


    @track_user_interaction
    async def gold_dollar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Scrapes gold and dollar prices and sends them to the user.
        Displays live prices from tgju.org and goldpricez.com, and includes a calculator button.
        Handles potential errors during price fetching.
        """
        user_id = update.effective_chat.id
        checking_msg = await context.bot.send_message(user_id, text='Checking site .... wait')

        try:
            latest_price = self.gold_db.get_latest_update()
            if not latest_price:
                raise Exception("Could not fetch prices")

            keyboard = [
                [InlineKeyboardButton(Messages.CALCULATOR_BUTTON, callback_data=f'{self.calculator.calculate_command}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=checking_msg.message_id,
                text=Messages.GOLD_PRICE_UPDATE.format(
                    time=latest_price.time_check_ir.strftime('%Y-%m-%d %H:%M'),
                    gold_18k_ir=latest_price.gold_18k_ir,
                    dollar_ir_rial=latest_price.dollar_ir_rial,
                    gold_18k_international_dollar=latest_price.gold_18k_international_dollar,
                    gold_18k_international_rial=latest_price.gold_18k_international_rial
                ),
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Gold price error: {e}")
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=checking_msg.message_id,
                text=Messages.PRICE_FETCH_ERROR)


    async def button(self, update, context):
        query = update.callback_query
        await query.answer()

        if query.data == f'{self.calculator.calculate_command}':
            await query.answer()
            conv_handler = self.calculator.get_calculated_price_conversation_handler()
            await conv_handler.trigger(update, context)
            await query.delete_message()


    def handler(self):
        return MessageHandler(filters.Regex(Messages.GOLD_DOLLAR_REGEX), self.gold_dollar)