import logging
from uuid import uuid4
from telegram import (Update, InlineQueryResultArticle,
                      InputTextMessageContent, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup)
from telegram.ext import InlineQueryHandler, filters, Application, ContextTypes, CommandHandler, ApplicationBuilder, \
    MessageHandler, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("/start")],
        [KeyboardButton("/caps Hello World")],
        [KeyboardButton("Just send text")]
    ]
    # keyboard = [
    #     [InlineKeyboardButton("Start", callback_data="/start")],
    #     [InlineKeyboardButton("Uppercase Text", callback_data="/caps Hello World")],
    #     [InlineKeyboardButton("Echo", callback_data="echo")]
    # ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    # reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!",
        reply_markup=reply_markup)


# Add a handler for button callbacks
# async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#
#     if query.data == "echo":
#         await query.edit_message_text(text="Now send me any text to echo")
#     elif query.data.startswith("/"):
#         # Simulate command execution
#         update.message = update.effective_message
#         update.message.text = query.data
#         if query.data.startswith("/caps"):
#             await caps(update, context)
#         elif query.data.startswith("/start"):
#             await start(update, context)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Caps",
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, that command is not defined")


if __name__ == "__main__":
    application = ApplicationBuilder().token("7651582199:AAHj9Ib_NOXga_iOZiQ5G9dD4pfC5AuFr0U").build()

    start_handler = CommandHandler("start", start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    inline_caps_handler = InlineQueryHandler(inline_caps)
    # button_handler = CallbackQueryHandler(button)
    #last
    unknown_handler = MessageHandler(filters.COMMAND, unknown)


    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)
    # application.add_handler(button_handler)
    #last
    application.add_handler(unknown_handler)

    application.run_polling()