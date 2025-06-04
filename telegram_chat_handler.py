from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters,CallbackQueryHandler,CommandHandler, filters
import time
from datetime import datetime, timedelta
from data_base import ChatDatabase, UserDatabase

from chat_random_test import user_sessions


# a leave and a goffy name option
# kasaii ke online ya 15 min online boodan beheshoon ye request bere hatman nabayad link dashte bashan


#todo 1-chat nashenas(done) 2-message nashenas
# 3-sakht link darkhast chat 4-random chat to app
# 5-sakht group chat nashensa ba esme mostaar
# 6-sakhte chat ba ai
# 7-match up be vasile ai

# todo link ke mifreste axe profile va description nadare bebin mishe doross kard
# todo get connected with db
#  oh there is alot of connection with db should take care


class AnonymousChat:
    def __init__(self):
        self.start_command = "start"
        self.leave_command = 'leave'
        self.secret_command = 'secret_chat'
        self.delete_command = 'confirm_delete'
        self.db = ChatDatabase()
        self.user_db = UserDatabase()

    # --- 1. Start ---
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("started anom chat")
        user_id = update.effective_user.id
        token = f'anonymously_chat-{abs(hash(str(user_id + time.time())))}'
        self.db.add_link(token, user_id, max_uses=1)
        bot_username = (await context.bot.get_me()).username
        deep_link = f'https://telegram.me/{bot_username}?text={token}'


        keyboard = [
            [
                InlineKeyboardButton("Share this link!!", url=f'https://t.me/share/url?url={deep_link}'),
            ]
        ]
        await update.message.reply_text(
            f"🔗 Your private chat link:\n`{token}`\n\n"
            "Share it to let others chat with you anonymously!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # --- 2. Join Chat via Link ---
    async def handle_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        if self.db.get_link(text):
            partner_id = self.db.get_link_owner(text)
            if user_id == partner_id:
                await update.message.reply_text("❌ You can't chat with yourself!")
                #return
            self.user_db.add_or_update_user(user_id, context.user_data)
            self.db.create_user_session(user_id)
            self.db.set_partnership(user_id, partner_id)
            self.db.decrement_link_use(text)
            keyboard = [
                [
                    KeyboardButton(f'/{self.leave_command}'),
                    KeyboardButton(f'/{self.secret_command}'),
                ]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard)
            await context.bot.send_message(
                partner_id,
                "🔄 A stranger has joined your chat! Say hello :)",
                reply_markup=reply_markup
            )
            await update.message.reply_text("🔄 Connected to a stranger! Start chatting.",
                                            reply_markup=reply_markup)

        else:
            await update.message.reply_text("❌ The link is wrong or has been expire")
            #return

    # --- 3. Relay Messages Anonymously ---
    async def reply_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.db.get_partner_id(user_id):
            await update.message.reply_text("⚠️ You're not doing anything. Do somthing /start")
            return

        partner_id = self.db.get_partner_id(user_id)
        message = update.message




        reply_to_id = None

        try:
            send_msg = None

            #handling reply
            if message.reply_to_message:
                reply_msg_id = message.reply_to_message.message_id

                reply_to_id = self.db.get_msg_id_by_robot_msg(reply_msg_id)
                if not reply_to_id:
                    reply_to_id = self.db.get_msg_id_by_user_msg(reply_msg_id)

            if message.text:
                send_msg = await context.bot.send_message(partner_id, f"👤: {message.text}", reply_to_message_id=reply_to_id)
            elif message.photo:
                send_msg = await context.bot.send_photo(partner_id, photo=message.photo[-1].file_id,
                                                        caption=f"👤: {message.caption}" if message.caption else None,
                                                        reply_to_message_id=reply_to_id,
                                                        has_spoiler=self.db.get_user_session(user_id).secret_chat,
                                                        protect_content=self.db.get_user_session(user_id).secret_chat)
            elif message.video:
                send_msg = await context.bot.send_video(
                    partner_id,
                    video=update.message.video.file_id,
                    caption=f"👤: {update.message.caption}" if update.message.caption else None,
                    reply_to_message_id=reply_to_id,
                    has_spoiler=self.db.get_user_session(user_id).secret_chat,
                    protect_content=self.db.get_user_session(user_id).secret_chat,
                    supports_streaming=self.db.get_user_session(user_id).secret_chat

            )

            elif message.audio:
                send_msg = await context.bot.send_audio(
                    partner_id,
                    audio=update.message.audio.file_id,
                    caption=f"👤: {update.message.caption}" if update.message.caption else None,
                    reply_to_message_id=reply_to_id,
                    has_spoiler=self.db.get_user_session(user_id).secret_chat,
                    protect_content=self.db.get_user_session(user_id).secret_chat,
            )

            elif message.document:
                send_msg = await context.bot.send_document(
                    partner_id,
                    document=update.message.document.file_id,
                    caption=f"👤: {update.message.caption}" if update.message.caption else None,
                    reply_to_message_id=reply_to_id,
                    has_spoiler=self.db.get_user_session(user_id).secret_chat,
                    protect_content=self.db.get_user_session(user_id).secret_chat,
            )

            elif update.message.sticker:  # Stickers

                send_msg=await context.bot.send_sticker(
                            partner_id,
                            sticker=update.message.sticker.file_id,
                            reply_to_message_id=reply_to_id
                        )
            elif update.message.voice:  # Voice messages

                send_msg = await context.bot.send_voice(
                            partner_id,
                            voice=update.message.voice.file_id,
                            reply_to_message_id=reply_to_id,
                            protect_content=self.db.get_user_session(user_id).secret_chat,
                        )

            if send_msg and hasattr(send_msg, "message_id"):

                self.db.map_message(message.message_id, send_msg.message_id, user_id, partner_id, msg_txt=message.text)

        except Exception as e:
            print(f"Error sending message xxx1: {e}")

    # --- 4. Leave Chat ---
    async def leave_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if self.db.get_partner_id(user_id):
            partner_id = self.db.get_partner_id(user_id)
            self.db.remove_partnership(user_id)
            keyboard = [[InlineKeyboardButton("Confirm Delete All", callback_data="confirm_delete")]]
            self.db.secret_chat_toggle(user_id, hand_change=False)
            # notify partner
            await context.bot.send_message(partner_id, "❌ Your partner has left the chat.",reply_markup=InlineKeyboardMarkup(keyboard))
            await update.message.reply_text("✅ You've left the chat. Use /start to generate a new link.\n\n⚠️ Delete ALL your sent messages?",reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text("⚠️ You're not in an active chat.")

    # --- 5. edit Chat ---
    async def handle_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.db.get_user_session(user_id)
        partner_id = self.db.get_partner_id(user_id)
        # if user_id not in self.user_sessions or not self.user_sessions[user_id]['partner']:
        #     return
        # partner_id = self.user_sessions[user_id]['partner']
        edited_message = update.edited_message
        try:
            original_msg_id = edited_message.message_id
            partner_msg_id = self.db.get_msg_id_by_user_msg(original_msg_id)

            # partner_msg_id = self.user_sessions[user_id].get('message_map', {}).get(original_msg_id)

            if not partner_msg_id:
                return


            if edited_message.text:
                await context.bot.edit_message_text(
                    chat_id=partner_id,
                    message_id=partner_msg_id,
                    text=f"✏️👤: {edited_message.text}"
                )
            elif edited_message.caption:
                await context.bot.edit_message_caption(
                    chat_id=partner_id,
                    message_id=partner_msg_id,
                    caption=f"✏️👤: {edited_message.caption}"
                )
        except Exception as e:
            print(f"Error forwarding edited message: {e}")

    # --- 6. Delete perv Chat ---
    async def delete_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        # if user_id not in self.user_sessions or not self.user_sessions[user_id].get('perv_partner'):
        #     await query.edit_message_text("⚠️ You were not in an active chat.")
        #     return

        perv_partner_id = self.db.get_user_session(user_id).perv_partner_id
        if not perv_partner_id:
            await query.edit_message_text("⚠️ You were not in an active chat.")
            return

        deleted_count = 0
        failed_count = 0

        try:
            await query.edit_message_text("🗑️ Deleting your messages from previous chat...")

            messages_to_delete = self.db.get_previous_partner_messages(user_id, perv_partner_id)
            for maped in messages_to_delete:
                msg_id = maped.bot_message_id
                try:
                    await context.bot.delete_message(chat_id=perv_partner_id,
                                                     message_id=msg_id)
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete message from partner {msg_id}: {e}")
                    failed_count += 1

            # messages_to_delete = list(self.user_sessions[user_id]['reverse_map'].values())
            # for msg_id in messages_to_delete:
            #     try:
            #         await context.bot.delete_message(chat_id=user_id,
            #                                          message_id=msg_id)




            # self.user_sessions[user_id]['message_map'] = {}
            # self.user_sessions[user_id]['reverse_map'] = {}

            # Notify user
            status_msg = f"🗑️ Deleted {deleted_count} messages"
            if failed_count > 0:
                status_msg += f" ({failed_count} failed)"

            await query.edit_message_text(status_msg)

            # Optionally notify partner
            if deleted_count > 0:
                try:
                    await context.bot.send_message(
                        perv_partner_id,
                        "⚠️ Your partner has deleted their messages"
                    )
                except Exception as e:
                    print(f"Couldn't notify partner: {e}")

        except Exception as e:
            print(f"Error in delete_handler: {e}")
            await query.edit_message_text("❌ Error deleting messages")

    # --- 7. On and off secret Chat ---
    async def secret_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        partner_id = self.db.get_partner_id(user_id)
        if not self.db.secret_chat_toggle(user_id):
            await update.message.reply_text("⚠️ You're not in an active chat.")
            return

        # partner_id = self.user_sessions[user_id]['partner']
        # # Ensure both users have consistent secret mode
        # new_mode = not self.user_sessions[user_id].get('secret_chat', False)

        # Update both users
        # for uid in [user_id, partner_id]:
        #     self.user_sessions[uid]['secret_chat'] = new_mode

        status = "activated 🔒" if self.db.secret_chat_toggle(user_id) else "deactivated 🔓"
        secret_note = "\n\nℹ️ Media will be blurred and protected from saving." if self.db.secret_chat_toggle(user_id) else ""

        # Notify both users
        await context.bot.send_message(
            user_id,
            f"Secret mode {status} for your chat.{secret_note}",
            parse_mode="Markdown")
        await context.bot.send_message(
            partner_id,
            f"Secret mode {status} for your partner chat.{secret_note}",
            parse_mode="Markdown")

    # ---  handlers ---
    def anonymously_chat_handlers(self):
        """user app.add_handlers"""

        return [
            CommandHandler(f'{self.start_command}', self.start),
            CommandHandler(f"{self.leave_command}", self.leave_chat),
            CommandHandler(f"{self.secret_command}", self.secret_toggle),

            CallbackQueryHandler(self.delete_handler, pattern="^confirm_delete$"),

            MessageHandler(filters.TEXT & filters.Regex(r'^anonymously_chat-'), self.handle_link),
            MessageHandler(
                filters.ALL & ~filters.COMMAND & ~filters.Regex(r'^anonymously_msg-') & ~filters.Regex(r'^anonymously_chat-') & ~filters.UpdateType.EDITED,
                self.reply_message
            ),
            MessageHandler(
                filters.ALL & ~filters.COMMAND & filters.UpdateType.EDITED,
                self.handle_edit
            )
        ]
#todo make the secret message
class AnonymousMessage:
    def __init__(self):
        self.start_command = "start"
        self.leave_command = 'leave'
        self.secret_command = 'secret_msg'
        self.delete_command = 'confirm_delete'
        self.db = ChatDatabase()
        self.user_db = UserDatabase()

    # --- 1. Start ---
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("started anom MSG")
        user_id = update.effective_user.id
        token = f'anonymously_msg-{abs(hash(str(user_id + time.time())))}'
        self.db.add_link(token, user_id)
        bot_username = (await context.bot.get_me()).username
        deep_link = f'https://telegram.me/{bot_username}?text={token}'

        keyboard = [
            [
                InlineKeyboardButton("Share this link!!", url=f'https://t.me/share/url?url={deep_link}'),
            ]
        ]
        await update.message.reply_text(
            f"🔗 Your private Message link:\n`{token}`\n\n"
            "Share it to let others can send you anonymous message to you anonymously!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # --- 2. Join Chat via Link ---
    async def handle_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        print('handling_link')
        if self.db.get_link(text):
            partner_id = self.db.get_link_owner(text)
            if user_id == partner_id:
                await update.message.reply_text("❌ You can't chat with yourself!")
                # return
            self.user_db.add_or_update_user(user_id, context.user_data)
            self.db.create_user_session(user_id)
            self.db.add_partner(user_id, partner_id)
            self.db.decrement_link_use(text)
            keyboard = [
                [
                    KeyboardButton(f'/{self.leave_command}'),
                    KeyboardButton(f'/{self.secret_command}'),
                ]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard)
            # await context.bot.send_message(
            #     partner_id,
            #     "🔄 A stranger has joined your chat! Say hello :)",
            #     reply_markup=reply_markup
            # )
            await update.message.reply_text("🔄 Connected to a stranger! Start chatting.",
                                            reply_markup=reply_markup)

        else:
            await update.message.reply_text("❌ The link is wrong or has been expire")
            # return
    # --- 3. On and off secret Chat ---
    async def secret_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        partner_id = self.db.get_partner_id(user_id)
        if not self.db.secret_chat_toggle(user_id):
            await update.message.reply_text("⚠️ You're not in an active chat.")
            return

        status = "activated 🔒" if self.db.secret_chat_toggle(user_id) else "deactivated 🔓"
        secret_note = "\n\nℹ️ Media will be blurred and protected from saving." if self.db.secret_chat_toggle(
            user_id) else ""

        # Notify both users
        await context.bot.send_message(
            user_id,
            f"Secret mode {status} for your chat.{secret_note}",
            parse_mode="Markdown")

    # --- 4. leave ---
    async def leave_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.db.remove_partner(user_id)
        await context.bot.send_message(user_id, text="✅ You've left the Messaging")

    # ---  handlers ---
    def anonymously_msg_handlers(self):
        """user app.add_handlers"""

        return [
            CommandHandler(f'{self.start_command}', self.start),
            CommandHandler(f"{self.leave_command}", self.leave_chat),
            CommandHandler(f"{self.secret_command}", self.secret_toggle),


            MessageHandler(filters.TEXT & filters.Regex(r'^anonymously_msg-'), self.handle_link),
            #todo handle reply only one needed it is look like should be higher

        ]