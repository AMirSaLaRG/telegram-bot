import logging
from telegram import (Update, InlineQueryResultArticle,
                      InputTextMessageContent, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, ReplyKeyboardRemove,)
from telegram.ext import (InlineQueryHandler, filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler,
                          ConversationHandler)
from telegram_conversations import Profile

import json
import os

os.makedirs("profiles", exist_ok=True)

# Ensure directory exists
os.makedirs("profiles", exist_ok=True)

profile = Profile()




logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if profile.check_exist_profile(update, context):
        keyboard= [
            [KeyboardButton("Random chat")],
            [
                KeyboardButton("Tehran location chat"),
                KeyboardButton("age chat"),

            ],
            [
                KeyboardButton('/profile')
            ]

        ]
    else:
        keyboard = [
            [KeyboardButton("Random chat")],
            [
                KeyboardButton("Tehran location chat"),
                KeyboardButton("age chat"),

            ],
            [
                KeyboardButton('/createprofile')
            ]

        ]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'start',
        reply_markup=reply_markup
    )





async def random_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "gender_filter" not in context.user_data:
        context.user_data['gender_filter']=[]
    gender_filter = context.user_data['gender_filter']
    keyboard = [

        [
            InlineKeyboardButton( f"{'✓ ' if 'male' in gender_filter else ''}Male", callback_data="gender: male"),
            InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}Female", callback_data="gender: female"),
        ],
        [
            InlineKeyboardButton('Done', callback_data="gender: done"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="random_chat mikahi",
        reply_markup=reply_markup,
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("gender:"):
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
            await update_buttons(query, context)

        elif action == "done":
            await gender_done(query, context)

#buttons functions :
async def update_buttons(query, context: ContextTypes.DEFAULT_TYPE):
    gender_filter = context.user_data['gender_filter']
    keyboard = [

        [
            InlineKeyboardButton(f"{'✓ ' if 'male' in gender_filter else ''}Male", callback_data="gender: male"),
            InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}Female", callback_data="gender: female"),
        ],
        [
            InlineKeyboardButton('Done', callback_data="gender: done"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="ehemm",
        reply_markup=reply_markup,
    )

async def gender_done(query, context: ContextTypes.DEFAULT_TYPE):
    await query.edit_message_text(
        text=f"u chosed gender {context.user_data['gender_filter']}"
    )
    #can clear that but why xD



if __name__ == "__main__":
    application = ApplicationBuilder().token("7651582199:AAHj9Ib_NOXga_iOZiQ5G9dD4pfC5AuFr0U").build()

    #create handler
    start_handler = CommandHandler("start", start)
    random_chat_handler = MessageHandler(filters.Regex("Random chat"), random_chat)
    my_profile = CommandHandler("profile", profile.show_profile)
        #button
    buttons_handler = CallbackQueryHandler(buttons)

    #add handler
    application.add_handler(start_handler)
    application.add_handler(random_chat_handler)
    application.add_handler(profile.get_profile_create_conversation_handler())
    application.add_handler(my_profile)

        #buttons
    application.add_handler(buttons_handler)

    application.run_polling()