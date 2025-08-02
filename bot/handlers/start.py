from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from bot.db.database import UserDatabase
from bot.utils.messages import Messages
from bot.handlers.intraction import track_user_interaction, interact



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
        print(update)
        self.user_db.get_user_data(update.effective_user.id, context.user_data)

        profile_button = Messages.PROFILE_BUTTON if context.user_data['name'] else Messages.CREATE_PROFILE_BUTTON
        keyboard = [
            [KeyboardButton(Messages.CHAT_BUTTON)],
            [
                KeyboardButton(Messages.TOROB_BUTTON),
                KeyboardButton(Messages.GOLD_DOLLAR_BUTTON),
            ],
            [KeyboardButton(profile_button)]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=Messages.START_MESSAGE,
            reply_markup=reply_markup
        )

    def handler(self):
        return CommandHandler(self.command, self.start)

