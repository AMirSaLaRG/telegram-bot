import logging
import re
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

        [KeyboardButton("Find ppl")],
        [
            KeyboardButton("Random chat"),
            KeyboardButton("Profile"),
        ],
        [KeyboardButton("Current location")],
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




async def find_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Location", callback_data="location_chat")],
        [InlineKeyboardButton("Age", callback_data="age_chat"),
        InlineKeyboardButton("Topic", callback_data="topic_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Based on",
        reply_markup=reply_markup
    )

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



# Add a handler for button callbacks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "location_chat":
        await location_handler(query, context)

    elif query.data == "age_chat":
        await query.edit_message_text(text="age search")

    elif query.data == "topic_chat":
        await query.edit_message_text(text="topic search")
    elif query.data.startswith("/"):
        # Simulate command execution
        update.message = update.effective_message
        update.message.text = query.data
        if query.data.startswith("/caps"):
            await caps(update, context)
        elif query.data.startswith("/start"):
            await start(update, context)

async def location_handler(query, context: ContextTypes.DEFAULT_TYPE):
    # Initialize if not exists
    if "selected_locations" not in context.user_data:
        context.user_data["selected_locations"] = set()
    # First show region selection
    selected = context.user_data['selected_locations']
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅ ' if 'north' in selected else ''}North",
                callback_data="loc_north"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if 'south' in selected else ''}South",
                callback_data="loc_south"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if 'east' in selected else ''}East",
                callback_data="loc_east"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅ ' if 'west' in selected else ''}West",
                callback_data="loc_west"
            )
        ],
        [InlineKeyboardButton("✅ Confirm", callback_data="loc_confirm")]
    ]
    await query.message.reply_text(
        "Select regions (multiple allowed):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def location_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Get current selections from context
    selected = context.user_data.get("selected_locations", set())

    if query.data.startswith("loc_"):
        region = query.data[4:]
        if region in ["north", "south", "east", "west"]:
            # Toggle selection
            if region in selected:
                selected.remove(region)
            else:
                selected.add(region)
            context.user_data["selected_locations"] = selected

            # RECREATE keyboard with visual feedback
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{'✅ ' if 'north' in selected else ''}North",
                        callback_data="loc_north"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{'✅ ' if 'south' in selected else ''}South",
                        callback_data="loc_south"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{'✅ ' if 'east' in selected else ''}East",
                        callback_data="loc_east"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"{'✅ ' if 'west' in selected else ''}West",
                        callback_data="loc_west"
                    )
                ],
                [InlineKeyboardButton("✅ Confirm", callback_data="loc_confirm")]
            ]

            # Update message with current selection AND NEW KEYBOARD
            selection_text = ", ".join(selected) if selected else "None"
            await query.edit_message_text(
                text=f"Select regions (multiple allowed):\nCurrent selection: {selection_text}",
                reply_markup=InlineKeyboardMarkup(keyboard)  # Use the new keyboard here
            )

        elif region == "confirm":
            if not selected:
                await query.answer("Please select at least one region!", show_alert=True)
            else:
                await query.edit_message_text(
                    text=f"✅ Selected regions: {', '.join(selected)}"
                )
                # Here you would add your location-based logic

if __name__ == "__main__":
    application = ApplicationBuilder().token("7651582199:AAHj9Ib_NOXga_iOZiQ5G9dD4pfC5AuFr0U").build()

    start_handler = CommandHandler("start", start)

    caps_handler = CommandHandler('caps', caps)
    inline_caps_handler = InlineQueryHandler(inline_caps)

    find_ppl_handler = MessageHandler(filters.Regex(r'^Find ppl$'), find_new)
    button_handler = CallbackQueryHandler(button)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    #last
    unknown_handler = MessageHandler(filters.COMMAND, unknown)


    application.add_handler(start_handler)

    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)
    application.add_handler(find_ppl_handler)
    application.add_handler(echo_handler)
    application.add_handler(button_handler)
    application.add_handler(CallbackQueryHandler(location_callback, pattern="^loc_"))
    #last
    application.add_handler(unknown_handler)

    application.run_polling()