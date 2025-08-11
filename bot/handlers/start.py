from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from bot.db.database import UserDatabase
from bot.handlers.intraction import track_user_interaction, interact

from bot.utils.messages_manager import messages as msg
# messages = msg(language=context.user_data['lan'])



class Start:
    def __init__(self):
        self.command = "start"
        self.user_db = UserDatabase()

    @track_user_interaction
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command.
        Initializes user session and displays the main keyboard based on user profile existence.
        """
        try:
            messages = msg(language=context.user_data['lan'])
        except Exception:
            context.user_data['language'] = 'en'
            context.user_data['lan'] = 'en'
            messages = msg()
        print(messages.CHAT_REGEX)

        self.user_db.get_user_data(update.effective_user.id, context.user_data)
        print(context.user_data['name'])

        complete_button = messages.COMPLETE_PROFILE_BUTTON if context.user_data['name'] == context.user_data['generated_id'] else ""
        keyboard = [
            [KeyboardButton(messages.CHAT_BUTTON)],
            [
                KeyboardButton(messages.TOROB_BUTTON),
                KeyboardButton(messages.GOLD_DOLLAR_BUTTON),
            ],
            [KeyboardButton(messages.PROFILE_BUTTON), KeyboardButton(complete_button)]
        ,
            [KeyboardButton(messages.EDIT_LANGUAGE_BUTTON)]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=messages.START_MESSAGE,
            reply_markup=reply_markup
        )

    def handler(self):
        return CommandHandler(self.command, self.start)

