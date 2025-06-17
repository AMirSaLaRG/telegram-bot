import datetime
import logging
from datetime import timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters,CallbackQueryHandler,CommandHandler, filters
import time
from data_base import ChatDatabase, UserDatabase
from random import choice
import asyncio


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

class UserMessage:
    def __init__(self):
        self.leave_command = "LeaveChat"
        self.secret_command= 'SecretChat'
        self.delete_command = 'ConfirmDeleteChat'
        self.command_create_anon_chat = 'createanonymousChat'
        self.command_create_anon_msg = 'createanonymousMsg'
        self.button_start_with_command = 'usermessagehandlerStarter'
        self.accept_chat_button_command = "acceptchat"
        self.deny_chat_button_command = 'denychat'
        self.db = ChatDatabase()
        self.user_db = UserDatabase()

    async def reply_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        name = "👤"
        if not self.db.get_partner_id(user_id):
            await update.message.reply_text("⚠️ You're not doing anything. Do somthing /start")
            return

        partner_id = self.db.get_partner_id(user_id)
        message = update.message

        reply_to_id = None
        msg_name = context.user_data.get('msg_name', "")

        if msg_name:
            name = msg_name

        try:
            send_msg = None

            # handling reply
            if message.reply_to_message:
                reply_msg_id = message.reply_to_message.message_id

                reply_to_id = self.db.get_msg_id_by_robot_msg(reply_msg_id)
                if not reply_to_id:
                    reply_to_id = self.db.get_msg_id_by_user_msg(reply_msg_id)

            if message.text:
                send_msg = await context.bot.send_message(partner_id, f"{name}: {message.text}",
                                                          reply_to_message_id=reply_to_id)
            elif message.photo:
                send_msg = await context.bot.send_photo(partner_id, photo=message.photo[-1].file_id,
                                                        caption=f"{name}: {message.caption}" if message.caption else None,
                                                        reply_to_message_id=reply_to_id,
                                                        has_spoiler=self.db.get_user_session(user_id).secret_chat,
                                                        protect_content=self.db.get_user_session(user_id).secret_chat)
            elif message.video:
                send_msg = await context.bot.send_video(
                    partner_id,
                    video=update.message.video.file_id,
                    caption=f"{name}: {update.message.caption}" if update.message.caption else None,
                    reply_to_message_id=reply_to_id,
                    has_spoiler=self.db.get_user_session(user_id).secret_chat,
                    protect_content=self.db.get_user_session(user_id).secret_chat,
                    supports_streaming=self.db.get_user_session(user_id).secret_chat

                )

            elif message.audio:
                send_msg = await context.bot.send_audio(
                    partner_id,
                    audio=update.message.audio.file_id,
                    caption=f"{name}: {update.message.caption}" if update.message.caption else None,
                    reply_to_message_id=reply_to_id,
                    has_spoiler=self.db.get_user_session(user_id).secret_chat,
                    protect_content=self.db.get_user_session(user_id).secret_chat,
                )

            elif message.document:
                send_msg = await context.bot.send_document(
                    partner_id,
                    document=update.message.document.file_id,
                    caption=f"{name}: {update.message.caption}" if update.message.caption else None,
                    reply_to_message_id=reply_to_id,
                    has_spoiler=self.db.get_user_session(user_id).secret_chat,
                    protect_content=self.db.get_user_session(user_id).secret_chat,
                )

            elif update.message.sticker:  # Stickers

                send_msg = await context.bot.send_sticker(
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
            if not self.db.get_partner_id(partner_id) and not self.db.get_partner_id(partner_id) == user_id:
                await self.leave_chat(update, context)
                await context.bot.send_message(user_id, text=f'Message sent to {partner_id}')

            user_saved_name = context.user_data.get('msg_name', "")
            if user_saved_name == name:
                context.user_data['msg_name'] = ''

        except Exception as e:
            print(f"Error sending message message reply: {e}")
    async def handle_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.db.get_user_session(user_id)
        partner_id = self.db.get_partner_id(user_id)
        edited_message = update.edited_message

        try:
            original_msg_id = edited_message.message_id
            partner_msg_id = self.db.get_msg_id_by_user_msg(original_msg_id)
            if not partner_msg_id:
                return
            if edited_message.text:
                await context.bot.edit_message_text(
                    chat_id=partner_id,
                    message_id=partner_msg_id,
                    text=f"✏️edited: {edited_message.text}"
                )
            elif edited_message.caption:
                await context.bot.edit_message_caption(
                    chat_id=partner_id,
                    message_id=partner_msg_id,
                    caption=f"✏️edited: {edited_message.caption}"
                )
        except Exception as e:
            print(f"Error forwarding edited message: {e}")
    async def delete_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        perv_partner_id = self.db.get_user_session(user_id).perv_partner_id
        if not perv_partner_id:
            await query.edit_message_text("⚠️ You were not in an active chat.")
            return
        deleted_count = 0
        failed_count = 0
        try:
            await query.edit_message_text("🗑️ Deleting your messages from previous chat...")

            messages_to_delete = self.db.get_previous_partner_messages(user_id, perv_partner_id)
            for mapped in messages_to_delete:
                msg_id = mapped.bot_message_id
                try:
                    await context.bot.delete_message(chat_id=perv_partner_id,
                                                     message_id=msg_id)
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete message from partner {msg_id}: {e}")
                    failed_count += 1
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
    async def leave_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_db.get_user_data(update.effective_user.id, context.user_data)
        user_id = update.effective_user.id
        if context.user_data.get('name', ''):
            keyboard2 = [
                [KeyboardButton("ChaT")],
                [
                    KeyboardButton("Torob price check"),
                    KeyboardButton("Gold & Dollar"),

                ],
                [
                    KeyboardButton('/profile')
                ]

            ]
        else:
            keyboard2 = [
                [KeyboardButton("ChaT")],
                [
                    KeyboardButton("Torob price check"),
                    KeyboardButton("Gold & Dollar"),

                ],
                [
                    KeyboardButton(f'/createprofile')
                ]

            ]
        reply_markup2 = ReplyKeyboardMarkup(keyboard2)
        if self.db.get_partner_id(user_id):
            partner_id = self.db.get_partner_id(user_id)
            if self.db.get_partner_id(partner_id) and self.db.get_partner_id(partner_id) == user_id:
                self.db.remove_partnership(user_id)
                keyboard = [[InlineKeyboardButton("Confirm Delete All", callback_data=self.delete_command)]]
                self.db.secret_chat_toggle(user_id, hand_change=False)

                # notify partner
                await context.bot.send_message(partner_id, "❌ Your partner has left the chat.",
                                               reply_markup=InlineKeyboardMarkup(keyboard))
                await context.bot.send_message(partner_id, "what else i can do for you.",
                                               reply_markup=reply_markup2)
                await update.message.reply_text("✅ You've left the chat."
                                                " Use /start to generate a new link.\n\n⚠️"
                                                " Delete ALL your sent messages?",
                                                reply_markup=InlineKeyboardMarkup(keyboard))
                await context.bot.send_message(user_id, "what else i can do for you.",
                                               reply_markup=reply_markup2)

                self.db.secret_chat_toggle(user_id, hand_change=False)
                self.db.secret_chat_toggle(partner_id, hand_change=False)
            else:
                self.db.remove_partner(user_id)
                self.db.secret_chat_toggle(user_id, hand_change=False)
                await context.bot.send_message(user_id, "what else i can do for you.",
                                               reply_markup=reply_markup2)


        else:
            await update.message.reply_text("⚠️ You're not in an active chat.")
    async def secret_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        partner_id = self.db.get_partner_id(user_id)
        if not partner_id:
            await update.message.reply_text("⚠️ You're not in an active chat.")
            return
        self.db.secret_chat_toggle(user_id)
        status = "activated 🔒" if self.db.get_user_session(user_id).secret_chat else "deactivated 🔓"

        secret_note = "\n\nℹ️ Media will be blurred and protected from saving." if (
            self.db.get_user_session(user_id).secret_chat) else ""
        # Notify both users
        if self.db.get_partner_id(partner_id) and self.db.get_partner_id(partner_id) == user_id:

            await context.bot.send_message(
                user_id,
                f"Secret mode {status} for your chat.{secret_note}",
                parse_mode="Markdown")
            await context.bot.send_message(
                partner_id,
                f"Secret mode {status} for your partner chat.{secret_note}",
                parse_mode="Markdown")
        else:
            await context.bot.send_message(
                user_id,
                f"Secret mode {status} for your chat.{secret_note}",
                parse_mode="Markdown")


    async def create_anonymous_chat_link(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
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
    async def create_anonymous_msg_link(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
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

    async def handle_link_chat(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        try:
            link_obj = self.db.get_link(text)
            if not link_obj:
                await update.message.reply_text(
                    "⚠️ This link is invalid or has expired.\n\n"
                    "Please ask your friend for a new link."
                )
                return

            partner_id = link_obj.owner_id
            if user_id == partner_id:
                await update.message.reply_text("❌ You can't chat with yourself!")
                return


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
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await context.bot.send_message(
                partner_id,
                "🔄 A stranger has joined your chat! Say hello :)",
                reply_markup=reply_markup
            )
            await update.message.reply_text("🔄 Connected to a stranger! Start chatting.",
                                            reply_markup=reply_markup)


        except Exception as e:

            logging.error(f"Link chat error: {e}")

            await update.message.reply_text(
                "⚠️ Something went wrong while processing your request.\n"
                "Please try again later."
            )
    async def handle_link_msg(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        context.user_data['msg_name'] = 'Some Person Over Link: '
        if self.db.get_link(text):
            partner_id = self.db.get_link_owner(text)
            if user_id == partner_id:
                await update.message.reply_text("❌ You can't chat with yourself!")
                return
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
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
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

    async def handle_random_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = context.user_data

        # Set user as looking for chat
        if not self.db.set_random_chat(user_id, True):
            await context.bot.send_message(user_id, text="Couldn't start random chat search")
            return


        # Get user's gender preferences
        gender_prefs = user_data.get('gender_filter', [])
        male_pref = 'male' in gender_prefs
        female_pref = 'female' in gender_prefs

        # Send searching message
        searching_msg = await context.bot.send_message(
            user_id,
            text='🔍 Searching for a random chat partner...'
        )

        # Search parameters
        start_time = datetime.datetime.now()
        search_timeout = 30  # seconds
        partner_found = False
        partner_id = None

        while not partner_found:
            # Check timeout
            if (datetime.datetime.now() - start_time).seconds > search_timeout:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=searching_msg.message_id,
                    text='⏳ Could not find a partner in time. Try again later!'
                )
                self.db.set_random_chat(user_id, False)
                return
            if self.db.get_partner_id(user_id):
                return
            # Get potential partners based on gender preferences
            ppl_for_chat = self.db.get_random_chaters(
                male=male_pref,
                female=female_pref
            )
            # Filter out self and invalid users
            #todo block users to and add
            valid_partners = [
                p for p in ppl_for_chat
                if p.user_id and p.user_id != user_id
            ]

            if valid_partners:
                partner = choice(valid_partners)
                partner_id = partner.user_id
                partner_found = True
            else:
                # Wait before next try
                await asyncio.sleep(2)

        # Establish partnership
        if partner_id and self.db.set_partnership(user_id, partner_id):
            # Update both users
            success_text = '✅ Connected! Start chatting now'
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=searching_msg.message_id,
                text=success_text
            )
            await context.bot.send_message(
                partner_id,
                text=success_text
            )

            # Cleanup
            self.db.set_random_chat(user_id, False)
            self.db.set_random_chat(partner_id, False)
        else:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=searching_msg.message_id,
                text='❌ Failed to establish connection. Please try again.'
            )
            self.db.set_random_chat(user_id, False)


    async def chat_request(self, update:Update, context: ContextTypes.DEFAULT_TYPE, target_id):
        user_id = update.effective_user.id
        if self.db.get_partner_id(user_id):
            await context.bot.send_message(user_id,
                                           text=f"You are in active chat first leave chat")

        elif self.db.get_user_session(target_id):
            if not self.db.get_partner_id(target_id):

                keyboard = [
                    [
                        InlineKeyboardButton("Accept", callback_data=f'{self.button_start_with_command}: {self.accept_chat_button_command}: {user_id}'),
                        InlineKeyboardButton("Deny", callback_data=f'{self.button_start_with_command}: {self.deny_chat_button_command}: {user_id}'),
                    ],

                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(user_id, text=f"you chat request for /chaT_{target_id} \n sent plz wait for answer")
                await context.bot.send_message(target_id, text=f'user: /chaT_{user_id} \nrequested to chat with you', reply_markup=reply_markup)
            else:
                await context.bot.send_message(user_id, text=f"user txting another user /chaT_{target_id} \n plz w8 until it is finished")
        else:
            await context.bot.send_message(user_id,
                                           text=f"invalid user id")



    async def buttons_set(self, update:Update, context:ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data.startswith(self.button_start_with_command):
            action = query.data.split(':')[1].strip().lower()
            target_id = query.data.split(':')[2].strip().lower()
            if action == self.accept_chat_button_command:
                await self.accept_chat(update, context, target_id)
            elif action == self.deny_chat_button_command:
                await self.deny_chat(update, context, target_id)



    async def accept_chat(self, update:Update, context:ContextTypes.DEFAULT_TYPE, target_id):
        user_id = update.effective_user.id
        query = update.callback_query
        if self.db.set_partnership(user_id, target_id):
            keyboard = [
                [KeyboardButton(f'/{self.leave_command}')],
                [KeyboardButton(f'/{self.secret_command}')],
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await query.edit_message_text(f'connected to /chaT_{target_id}')
            await context.bot.send_message(user_id, text='You can use buttons to leave or start secret chats', reply_markup=reply_markup)
            await context.bot.send_message(target_id, text=f'connected to /chaT_{user_id}',
                                           reply_markup=reply_markup)
        else:
            await context.bot.send_message(user_id, text=f'Could not find this user')

    async def deny_chat(self, update:Update, context:ContextTypes.DEFAULT_TYPE, target_id):
        user_id = update.effective_user.id
        await context.bot.send_message(user_id, text=f'/chaT_{target_id} got denied')
        await context.bot.send_message(target_id, text=f'/chaT_{user_id} did not accept your chat request')

    def message_handlers(self):
        return [
            CommandHandler(f'{self.command_create_anon_chat}', self.create_anonymous_chat_link),
            CommandHandler(f'{self.command_create_anon_msg}', self.create_anonymous_msg_link),
            CommandHandler(f"{self.secret_command}", self.secret_toggle),
            CallbackQueryHandler(self.delete_handler, pattern=f"^{self.delete_command}$"),
            MessageHandler(filters.TEXT & filters.Regex(r'^anonymously_chat-'), self.handle_link_chat),
            MessageHandler(filters.TEXT & filters.Regex(r'^anonymously_msg-'), self.handle_link_msg),
            CommandHandler(f"{self.leave_command}", self.leave_chat),
            MessageHandler(
                filters.ALL & ~filters.COMMAND & ~filters.Regex(r'^anonymously_msg-') & ~filters.Regex(
                    r'^anonymously_chat-') & ~filters.UpdateType.EDITED,
                self.reply_message
            ),
            MessageHandler(
                filters.ALL & ~filters.COMMAND & filters.UpdateType.EDITED,
                self.handle_edit
            ),


        ]



