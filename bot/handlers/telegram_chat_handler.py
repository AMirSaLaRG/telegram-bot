import datetime
import logging
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Message,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)
import time
from bot.db.database import ChatDatabase, UserDatabase, RelationshipManager
from random import choice
import asyncio
from bot.handlers.intraction import track_user_interaction
from bot.handlers.start import Start

from bot.utils.messages_manager import messages as msg
from bot.utils.messages_manager import languages as the_lans

# messages = msg(language=context.user_data['lan'])

# a leave and a goffy name option
# kasaii ke online ya 15 min online boodan beheshoon ye request bere hatman nabayad link dashte bashan


class UserMessage:
    """
    Handles various user messages and interactions for a Telegram bot,
    including anonymous chats, secret chats, message deletion, and link management.
    """

    def __init__(self):
        """
        Initializes the UserMessage handler with command strings and database connections.
        """
        # todo this look sass the messages check
        messages = msg()
        self.leave_command = messages.LEAVE_BUTTON
        self.secret_command = messages.SECRET_BUTTON
        self.delete_command = messages.DELETE_BUTTON

        self.button_start_with_command = messages.BUTTON_PREFIX
        self.accept_chat_button_command = messages.ACCEPT_CMD
        self.deny_chat_button_command = messages.DENY_CMD
        self.db = ChatDatabase()
        self.db_rel = RelationshipManager()
        self.user_db = UserDatabase()

    def _get_reply_to_id(self, message: Message) -> Optional[int]:
        """Resolves reply_to_message_id for cross-chat replies."""
        if not message.reply_to_message:
            return None

        return self.db.get_msg_id_by_robot_msg(
            message.reply_to_message.message_id
        ) or self.db.get_msg_id_by_user_msg(message.reply_to_message.message_id)

    async def _handle_text_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """Handles text messages."""
        return await context.bot.send_message(
            partner_id,
            f"{name}: {update.message.text}",
            reply_to_message_id=reply_to_id,
        )

    async def _handle_photo_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """Handles photo messages."""
        return await context.bot.send_photo(
            partner_id,
            photo=update.message.photo[-1].file_id,
            caption=(
                f"{name}: {update.message.caption}" if update.message.caption else None
            ),
            reply_to_message_id=reply_to_id,
            has_spoiler=secret_chat,
            protect_content=secret_chat,
        )

    async def _handle_video_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """handles vide messages"""
        return await context.bot.send_video(
            partner_id,
            video=update.message.video.file_id,
            caption=(
                f"{name}: {update.message.caption}" if update.message.caption else None
            ),
            reply_to_message_id=reply_to_id,
            has_spoiler=secret_chat,
            protect_content=secret_chat,
            supports_streaming=secret_chat,
        )

    async def _handle_video_note_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """Handles circular video messages."""
        return await context.bot.send_video_note(
            chat_id=partner_id,
            video_note=update.message.video_note.file_id,
            reply_to_message_id=reply_to_id,
            protect_content=secret_chat,
        )

    async def _handle_audio_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """handles audio messages"""
        return await context.bot.send_audio(
            partner_id,
            audio=update.message.audio.file_id,
            caption=(
                f"{name}: {update.message.caption}" if update.message.caption else None
            ),
            reply_to_message_id=reply_to_id,
            protect_content=secret_chat,
        )

    async def _handle_document_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """Handles document messages without has_spoiler parameter."""
        kwargs = {
            "chat_id": partner_id,
            "document": update.message.document.file_id,
            "reply_to_message_id": reply_to_id,
            "protect_content": secret_chat,
        }

        if update.message.caption:
            kwargs["caption"] = f"{name}: {update.message.caption}"

        return await context.bot.send_document(**kwargs)

    async def _handle_sticker_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """handles sticker messages"""
        return await context.bot.send_sticker(
            partner_id,
            sticker=update.message.sticker.file_id,
            reply_to_message_id=reply_to_id,
        )

    async def _handle_voice_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
        reply_to_id: Optional[int],
        secret_chat: bool,
    ) -> Optional[Message]:
        """handles voice messages"""
        return await context.bot.send_voice(
            partner_id,
            voice=update.message.voice.file_id,
            reply_to_message_id=reply_to_id,
            protect_content=secret_chat,
        )

    async def _send_message_to_partner(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        partner_id: int,
        name: str,
    ) -> Optional[Message]:
        """centralized message dispatch based on type."""
        if not update.message or not hasattr(update, "effective_user"):
            return None
        handler_map = {
            "text": self._handle_text_message,
            "photo": self._handle_photo_message,
            "video": self._handle_video_message,
            "video_note": self._handle_video_note_message,
            "audio": self._handle_audio_message,
            "document": self._handle_document_message,
            "sticker": self._handle_sticker_message,
            "voice": self._handle_voice_message,
        }
        message = update.message
        msg_type = next((t for t in handler_map if getattr(message, t, None)), None)

        if not msg_type:
            return None

        secret_chat = self.db.get_user_session(update.effective_user.id).secret_chat
        reply_to_id = self._get_reply_to_id(message)

        return await handler_map[msg_type](
            update, context, partner_id, name, reply_to_id, secret_chat
        )

    # async def _check_partner_status(self, partner_id, user_id, update, context):
    #     if not self.db.get_partner_id(partner_id) and not self.db.get_partner_id(partner_id) == user_id:
    #         await self.leave_chat(update, context)
    #         await context.bot.send_message(user_id, text=f'Message sent to {partner_id}')

    @track_user_interaction
    async def reply_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles incoming messages and forwards them to the connected chat partner.
        Supports text, photo, video, audio, document, sticker, and voice messages.
        Also handles replies and secret chat protections.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        if not (partner_id := self.db.get_partner_id(user_id)):
            await update.message.reply_text(messages.NOT_IN_CHAT)
            return
        try:
            name = context.user_data.get("msg_name", "👤")
            send_msg = await self._send_message_to_partner(
                update, context, partner_id, name
            )

            if send_msg and hasattr(send_msg, "message_id"):
                self.db.map_message(
                    update.message.message_id,
                    send_msg.message_id,
                    user_id,
                    partner_id,
                    msg_txt=update.message.text,
                )

            if (
                not self.db.get_partner_id(partner_id)
                and not self.db.get_partner_id(partner_id) == user_id
            ):
                await self.leave_chat(update, context)
                await context.bot.send_message(
                    user_id, text=f"Message sent to {partner_id}"
                )

            # Clear custom message name after sending if it was used
            user_saved_name = context.user_data.get("msg_name", "")
            if user_saved_name == name:
                context.user_data["msg_name"] = ""

        except Exception as e:
            print(f"Error sending message message reply: {e}")
            retry_keyboard = [
                [
                    InlineKeyboardButton(
                        messages.RETRY_BUTTON,
                        callback_data=f"retry_{update.message.message_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        messages.CANCEL_BUTTON, callback_data="cancel_failed_message"
                    )
                ],
            ]
            await update.message.reply_text(
                "⚠️ Failed to send message. Please try again.",
                reply_markup=InlineKeyboardMarkup(retry_keyboard),
            )

    async def handle_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles edited messages and updates the corresponding message in the partner's chat.
        Supports editing of text and captions.
        """
        user_id = update.effective_user.id
        self.db.get_user_session(user_id)  # Ensure user session is active/fetched
        partner_id = self.db.get_partner_id(user_id)
        edited_message = update.edited_message

        try:
            original_msg_id = edited_message.message_id
            # Get the partner's message ID corresponding to the edited message
            partner_msg_id = self.db.get_msg_id_by_user_msg(original_msg_id)
            if not partner_msg_id:
                return  # No corresponding message found in partner's chat
            if edited_message.text:
                await context.bot.edit_message_text(
                    chat_id=partner_id,
                    message_id=partner_msg_id,
                    text=f"✏️edited: {edited_message.text}",
                )
            elif edited_message.caption:
                await context.bot.edit_message_caption(
                    chat_id=partner_id,
                    message_id=partner_msg_id,
                    caption=f"✏️edited: {edited_message.caption}",
                )
        except Exception as e:
            print(f"Error forwarding edited message: {e}")

    async def delete_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the "Confirm Delete All" callback, deleting all messages sent by the user
        in a previous chat with a partner.
        """
        messages = msg(language=context.user_data["lan"])
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query
        user_id = query.from_user.id
        perv_partner_id = self.db.get_user_session(
            user_id
        ).perv_partner_id  # Get previous partner ID
        if not perv_partner_id:
            await query.edit_message_text("⚠️ You were not in an active chat.")
            return
        deleted_count = 0
        failed_count = 0
        try:
            await query.edit_message_text(
                "🗑️ Deleting your messages from previous chat..."
            )

            messages_to_delete = self.db.get_previous_partner_messages(
                user_id, perv_partner_id
            )
            for mapped in messages_to_delete:
                msg_id = (
                    mapped.bot_message_id
                )  # Get the bot's message ID (in partner's chat)
                try:
                    await context.bot.delete_message(
                        chat_id=perv_partner_id, message_id=msg_id
                    )
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete message from partner {msg_id}: {e}")
                    failed_count += 1
            status_msg = messages.MESSAGE_DELETED.format(deleted_count=deleted_count)
            if failed_count > 0:
                status_msg += messages.DELETE_FAILED.format(failed_count=failed_count)

            await query.edit_message_text(status_msg)

            # Optionally notify partner that messages have been deleted
            if deleted_count > 0:
                try:
                    await context.bot.send_message(
                        perv_partner_id, messages.DELETE_NOTIFICATION
                    )
                except Exception as e:
                    print(f"Couldn't notify partner: {e}")
        except Exception as e:
            print(f"Error in delete_handler: {e}")
            await query.edit_message_text(messages.DELETE_ERROR)

    async def leave_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Allows a user to leave an active chat. It notifies the partner,
        removes the partnership, and offers the option to delete messages.
        """
        messages = msg(language=context.user_data["lan"])
        self.user_db.get_user_data(
            update.effective_user.id, context.user_data
        )  # Load user data for keyboard layout
        user_id = update.effective_user.id
        # Define keyboard options based on whether the user has a profile name

        # Check if the user is currently in a chat
        if self.db.get_partner_id(user_id):
            partner_id = self.db.get_partner_id(user_id)
            # Check if the partnership is mutual (both users have each other as partners)
            if (
                self.db.get_partner_id(partner_id)
                and self.db.get_partner_id(partner_id) == user_id
            ):
                self.db.remove_partnership(
                    user_id
                )  # Remove partnership from both sides
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Confirm Delete All", callback_data=self.delete_command
                        )
                    ]
                ]
                self.db.secret_chat_toggle(
                    user_id, hand_change=False
                )  # Disable secret chat for the user

                # Notify partner that the chat has ended
                await context.bot.send_message(
                    partner_id,
                    messages.PARTNER_LEFT,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )  # Offer partner message deletion option

                # Notify the user and offer message deletion option
                await update.message.reply_text(
                    messages.CHAT_LEFT, reply_markup=InlineKeyboardMarkup(keyboard)
                )


                # Ensure secret chat is toggled off for both users
                self.db.secret_chat_toggle(user_id, hand_change=False)
                self.db.secret_chat_toggle(partner_id, hand_change=False)
            else:
                # If only one-sided partnership, just remove the user's partner entry
                self.db.remove_partner(user_id)
                self.db.secret_chat_toggle(user_id, hand_change=False)
                await context.bot.send_message(
                    user_id, "what else i can do for you.",
                )



        else:
            # If user is not in any active chat

            await update.message.reply_text(messages.NOT_IN_CHAT)
        await Start().start(update, context)
    async def secret_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Toggles the 'secret mode' for the current chat, blurring and protecting media.
        Notifies both chat participants of the change.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        partner_id = self.db.get_partner_id(user_id)
        if not partner_id:
            await update.message.reply_text("⚠️ You're not in an active chat.")
            return
        self.db.secret_chat_toggle(user_id)  # Toggle secret chat status for the user
        status = (
            messages.SECRET_MODE_ACTIVATED
            if self.db.get_user_session(user_id).secret_chat
            else messages.SECRET_MODE_DEACTIVATED
        )

        secret_note = (
            messages.SECRET_MODE_NOTE
            if self.db.get_user_session(user_id).secret_chat
            else ""
        )
        # Notify both users about the secret mode status change
        if (
            self.db.get_partner_id(partner_id)
            and self.db.get_partner_id(partner_id) == user_id
        ):
            await context.bot.send_message(
                user_id,
                f"Secret mode {status} for your chat.{secret_note}",
                parse_mode="Markdown",
            )
            await context.bot.send_message(
                partner_id,
                f"Secret mode {status} for your partner chat.{secret_note}",
                parse_mode="Markdown",
            )
        else:
            # If partner is not mutually connected (e.g., one-sided link chat)
            await context.bot.send_message(
                user_id,
                f"Secret mode {status} for your chat.{secret_note}",
                parse_mode="Markdown",
            )

    @track_user_interaction
    async def create_anonymous_chat_link(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Generates a unique deep link for an anonymous chat request.
        This link allows another user to initiate an anonymous chat with the link creator.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        # Generate a unique token for the anonymous chat link
        token = f"anonymously_chat-{abs(hash(str(user_id + time.time())))}"
        self.db.add_link(
            token, user_id, max_uses=1
        )  # Add the link to the database with 1 max use
        bot_username = (await context.bot.get_me()).username
        deep_link = f"https://telegram.me/{bot_username}?text={token}"

        keyboard = [
            [
                InlineKeyboardButton(
                    messages.SHARE_BUTTON, url=f"https://t.me/share/url?url={deep_link}"
                ),
            ]
        ]
        await update.message.reply_text(
            messages.ANON_CHAT_LINK.format(token=token),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    @track_user_interaction
    async def create_anonymous_msg_link(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Generates a unique deep link for sending anonymous messages.
        This link allows another user to send anonymous messages to the link creator.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        # Generate a unique token for the anonymous message link
        token = f"anonymously_msg-{abs(hash(str(user_id + time.time())))}"
        self.db.add_link(
            token, user_id
        )  # Add the link to the database (no max uses specified, implying unlimited)
        bot_username = (await context.bot.get_me()).username
        deep_link = f"https://telegram.me/{bot_username}?text={token}"

        keyboard = [
            [
                InlineKeyboardButton(
                    messages.SHARE_BUTTON, url=f"https://t.me/share/url?url={deep_link}"
                ),
            ]
        ]
        await update.message.reply_text(
            messages.ANON_MSG_LINK.format(token=token),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    @track_user_interaction
    async def handle_link_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles an incoming message containing an anonymous chat link.
        Establishes a chat partnership if the link is valid and not used by the owner.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        text = update.message.text.strip()
        try:
            link_obj = self.db.get_link(text)  # Retrieve link object from database
            if not link_obj:
                await update.message.reply_text(messages.INVALID_LINK)
                return

            partner_id = link_obj.owner_id  # Get the owner of the link
            if user_id == partner_id:
                await update.message.reply_text(messages.SELF_CHAT_ERROR)
                return

            self.user_db.add_or_update_user(
                user_id, context.user_data
            )  # Add or update user data
            self.db.create_user_session(
                user_id
            )  # Create a user session for the new chat
            self.db.set_partnership(user_id, partner_id)  # Establish mutual partnership
            self.db.decrement_link_use(text)  # Decrement link usage count

            keyboard = [
                [
                    KeyboardButton(f"/{self.leave_command}"),
                    KeyboardButton(f"/{self.secret_command}"),
                ]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            # Notify both users that they are connected
            await context.bot.send_message(
                partner_id, messages.STRANGER_JOINED, reply_markup=reply_markup
            )
            await update.message.reply_text(
                messages.CONNECTED_STRANGER, reply_markup=reply_markup
            )

        except Exception as e:
            logging.error(f"Link chat error: {e}")
            await update.message.reply_text(
                "⚠️ Something went wrong while processing your request.\n"
                "Please try again later."
            )

    @track_user_interaction
    async def handle_link_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles an incoming message containing an anonymous message link.
        Sets up a one-sided connection for sending anonymous messages.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        text = update.message.text.strip()
        context.user_data["msg_name"] = (
            "Some Person Over Link: "  # Set a default anonymous name for message sender
        )
        if self.db.get_link(text):  # Check if the link is valid
            partner_id = self.db.get_link_owner(text)  # Get the owner of the link
            if user_id == partner_id:
                await update.message.reply_text(messages.SELF_CHAT_ERROR)
                return
            self.user_db.add_or_update_user(user_id, context.user_data)
            self.db.create_user_session(user_id)
            self.db.add_partner(
                user_id, partner_id
            )  # Establish one-sided partnership for message sending
            self.db.decrement_link_use(text)  # Decrement link usage count
            keyboard = [
                [
                    KeyboardButton(f"/{self.leave_command}"),
                    KeyboardButton(f"/{self.secret_command}"),
                ]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            # This part is commented out in original code, but would notify the partner.
            # await context.bot.send_message(
            #     partner_id,
            #     "🔄 A stranger has joined your chat! Say hello :)",
            #     reply_markup=reply_markup
            # )
            await update.message.reply_text(
                messages.CONNECTED_STRANGER, reply_markup=reply_markup
            )

        else:
            await update.message.reply_text(messages.LINK_EXPIRED)
            # return

    async def handle_random_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Initiates a search for a random chat partner based on user gender preferences.
        Establishes a chat connection if a suitable partner is found within a timeout period.
        """
        messages = msg(language=context.user_data["lan"])
        # todo check the realtionship table and dont connect block pplz
        user_id = update.effective_user.id
        user_data = context.user_data

        # Set user as looking for chat in the database
        if not self.db.set_random_chat(user_id, True):
            await context.bot.send_message(user_id, text=messages.RANDOM_CHAT_ERROR)
            return

        # Get user's gender preferences for matching
        gender_prefs = user_data.get("gender_filter", [])
        context.user_data["gender_filter"] = []
        male_pref = "male" in gender_prefs
        female_pref = "female" in gender_prefs

        # Send a searching message to the user
        searching_msg = await context.bot.send_message(
            user_id, text=messages.SEARCHING_PARTNER
        )

        # Search parameters for timeout
        start_time = datetime.datetime.now()
        search_timeout = 30  # seconds
        partner_found = False
        partner_id = None

        keyboard = [
            [
                KeyboardButton(f"/{self.leave_command}"),
                KeyboardButton(f"/{self.secret_command}"),
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        while not partner_found:
            # Check for timeout
            if (datetime.datetime.now() - start_time).seconds > search_timeout:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=searching_msg.message_id,
                    text=messages.PARTNER_TIMEOUT,
                )
                self.db.set_random_chat(user_id, False)  # Stop searching for the user
                return
            # If user already connected, stop searching
            if self.db.get_partner_id(user_id):
                return
            # Get potential partners from the database based on preferences
            ppl_for_chat = self.db.get_random_chaters(
                male=male_pref, female=female_pref
            )
            # Filter out self and invalid users (e.g., already in chat, blocked)
            valid_partners = [
                p for p in ppl_for_chat if p.user_id and p.user_id != user_id
            ]

            if valid_partners:
                partner = choice(
                    valid_partners
                )  # Choose a random partner from valid ones
                partner_id = partner.user_id
                partner_found = True
            else:
                # Wait before the next search attempt
                await asyncio.sleep(2)

        # Establish partnership if a partner is found
        if partner_id and self.db.set_partnership(user_id, partner_id):
            # Update searching message for the user who initiated the search
            await context.bot.send_message(
                user_id, text=messages.CONNECTED, reply_markup=reply_markup
            )
            # Notify the found partner
            await context.bot.send_message(
                partner_id, text=messages.CONNECTED, reply_markup=reply_markup
            )

            # Cleanup: set random chat status to False for both partners
            self.db.set_random_chat(user_id, False)
            self.db.set_random_chat(partner_id, False)
        else:
            # If connection failed after finding a partner (e.g., race condition)
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=searching_msg.message_id,
                text=messages.CONNECTION_FAILED,
            )
            self.db.set_random_chat(user_id, False)  # Stop searching for the user

    @track_user_interaction
    async def chat_request(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id
    ):
        """
        Sends a chat request to a specific user (target_id).
        Allows the target user to accept or deny the chat.
        """
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        if self.db_rel.is_block(target_id, user_id):
            await context.bot.send_message(
                user_id, text=messages.BLOCKED_FROM_USER_WARNING
            )
            return

        # Check if the requesting user is already in an active chat
        if self.db.get_partner_id(user_id):
            await context.bot.send_message(user_id, text=messages.ACTIVE_CHAT_WARNING)

        # Check if the target user has an active session
        elif self.db.get_user_session(target_id):
            # Check if the target user is not already in an active chat
            if not self.db.get_partner_id(target_id):
                keyboard = [
                    [
                        InlineKeyboardButton(
                            messages.ACCEPT_BUTTON,
                            callback_data=f"{messages.BUTTON_PREFIX}: {messages.ACCEPT_CMD}: {user_id}",
                        ),
                        InlineKeyboardButton(
                            messages.DENY_BUTTON,
                            callback_data=f"{messages.BUTTON_PREFIX}: {messages.DENY_CMD}: {user_id}",
                        ),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    user_id, text=messages.REQUEST_SENT.format(target_id=target_id)
                )
                await context.bot.send_message(
                    target_id,
                    text=messages.REQUEST_RECEIVED.format(user_id=user_id),
                    reply_markup=reply_markup,
                )
            else:
                await context.bot.send_message(
                    user_id, messages.BUSY_USER.format(target_id=target_id)
                )
        else:
            await context.bot.send_message(user_id, text=messages.INVALID_USER)

    async def buttons_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles callback queries from inline keyboard buttons, dispatching to specific handlers.
        Used for accepting or denying chat requests.
        """
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query

        if query.data.startswith("random_chat: gender: done"):
            await self.handle_random_chat(update, context)

        if query.data.startswith(self.button_start_with_command):
            # Parse action and target ID from callback data
            action = query.data.split(":")[1].strip().lower()
            target_id = query.data.split(":")[2].strip().lower()
            if action == self.accept_chat_button_command:
                await self.accept_chat(update, context, target_id)
            elif action == self.deny_chat_button_command:
                await self.deny_chat(update, context, target_id)

    async def accept_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id
    ):
        """
        Accepts an incoming chat request, establishing a mutual partnership.
        Notifies both users of the successful connection and provides chat controls.
        """
        user_id = update.effective_user.id
        query = update.callback_query
        if self.db.set_partnership(
            user_id, target_id
        ):  # Establish mutual partnership in database
            keyboard = [
                [KeyboardButton(f"/{self.leave_command}")],
                [KeyboardButton(f"/{self.secret_command}")],
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await query.edit_message_text(f"connected to /chaT_{target_id}")
            await context.bot.send_message(
                user_id,
                text="You can use buttons to leave or start secret chats",
                reply_markup=reply_markup,
            )
            await context.bot.send_message(
                target_id,
                text=f"connected to /chaT_{user_id}",
                reply_markup=reply_markup,
            )
        else:
            await context.bot.send_message(user_id, text=f"Could not find this user")

    async def deny_chat(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id
    ):
        """
        Denies an incoming chat request.
        Notifies both the requesting user and the denying user of the decision.
        """
        user_id = update.effective_user.id
        await context.bot.send_message(user_id, text=f"/chaT_{target_id} got denied")
        await context.bot.send_message(
            target_id, text=f"/chaT_{user_id} did not accept your chat request"
        )

    @track_user_interaction
    async def random_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Initiates the random chat setup, specifically for gender filtering.
        """
        messages = msg(language=context.user_data["lan"])
        if "gender_filter" not in context.user_data:
            # mael and female
            context.user_data["gender_filter"] = []

        gender_filter = context.user_data["gender_filter"]
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✓ ' if 'male' in gender_filter else ''}{messages.MALE_OPTION}",
                    callback_data="random gender: male",
                ),
                InlineKeyboardButton(
                    f"{'✓ ' if 'female' in gender_filter else ''}{messages.FEMALE_OPTION}",
                    callback_data="random gender: female",
                ),
            ],
            [
                InlineKeyboardButton(
                    messages.DONE_BUTTON, callback_data="random_chat: gender: done"
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=messages.RANDOM_CHAT_PROMPT,
            reply_markup=reply_markup,
        )

    @track_user_interaction
    async def chat_initiator_buttom(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the 'ChaT' button.
        Displays options related to chat functionalities (random, anonymous, advanced search).
        """
        messages = msg(language=context.user_data["lan"])
        keyboard = [
            [KeyboardButton(messages.RANDOM_CHAT_BUTTON)],
            [
                KeyboardButton(f"{messages.CREATE_ANON_CHAT}"),
                KeyboardButton(f"{messages.CREATE_ANON_MSG}"),
            ],
            [KeyboardButton(messages.ADVANCE_SEARCH_BUTTON)],
            [KeyboardButton("/start")],
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=messages.WHAT_YOU_LOOKING_FOR,
            reply_markup=reply_markup,
        )

    def get_handler_for_all_languages(self):
        languages = [key for key, value in the_lans.items()]
        handlers = []
        for lan in languages:
            messages = msg(language=lan)

            lan_handler = [
                MessageHandler(
                    filters.Regex(rf"^{messages.RANDOM_CHAT_BUTTON}$"), self.random_chat
                ),
                MessageHandler(
                    filters.Regex(messages.CHAT_REGEX), self.chat_initiator_buttom
                ),
                MessageHandler(
                    filters.Regex(rf"^{messages.CREATE_ANON_CHAT}"),
                    self.create_anonymous_chat_link,
                ),  # Handler for creating anonymous chat links
                MessageHandler(
                    filters.Regex(rf"^{messages.CREATE_ANON_MSG}"),
                    self.create_anonymous_msg_link,
                ),  # Handler for creating anonymous message links
                CommandHandler(
                    f"{self.secret_command}", self.secret_toggle
                ),  # Handler for toggling secret chat mode
                CallbackQueryHandler(
                    self.delete_handler, pattern=f"^{self.delete_command}$"
                ),  # Handler for confirming message deletion
                MessageHandler(
                    filters.TEXT & filters.Regex(r"^anonymously_chat-"),
                    self.handle_link_chat,
                ),  # Handler for processing anonymous chat links
                MessageHandler(
                    filters.TEXT & filters.Regex(r"^anonymously_msg-"),
                    self.handle_link_msg,
                ),  # Handler for processing anonymous message links
                CommandHandler(
                    f"{self.leave_command}", self.leave_chat
                ),  # Handler for leaving a chat
                MessageHandler(
                    filters.ALL & ~filters.COMMAND & filters.UpdateType.EDITED,
                    self.handle_edit,  # Handler for edited messages
                ),
            ]
            handlers += lan_handler

        constant_handlers = [
            MessageHandler(
                filters.ALL
                & ~filters.COMMAND
                & ~filters.Regex(r"^anonymously_msg-")
                & ~filters.Regex(r"^anonymously_chat-")
                & ~filters.UpdateType.EDITED,
                self.reply_message,  # Handler for all non-command, non-link, non-edited messages (for chat forwarding)
            ),
        ]
        handlers += constant_handlers
        print(handlers)
        return handlers

    # base handlers
    def message_handlers(self):
        """
        Returns a list of Telegram Bot API handlers for various commands and message types.
        These handlers link commands and message patterns to their corresponding asynchronous functions.
        """
        messages = msg()
        return [
            MessageHandler(filters.Regex(messages.RANDOM_CHAT_REGEX), self.random_chat),
            MessageHandler(
                filters.Regex(messages.CHAT_REGEX), self.chat_initiator_buttom
            ),
            CommandHandler(
                f"{messages.CREATE_ANON_CHAT}", self.create_anonymous_chat_link
            ),
            # Handler for creating anonymous chat links
            CommandHandler(
                f"{messages.CREATE_ANON_MSG}", self.create_anonymous_msg_link
            ),
            # Handler for creating anonymous message links
            CommandHandler(
                f"{self.secret_command}", self.secret_toggle
            ),  # Handler for toggling secret chat mode
            CallbackQueryHandler(
                self.delete_handler, pattern=f"^{self.delete_command}$"
            ),  # Handler for confirming message deletion
            MessageHandler(
                filters.TEXT & filters.Regex(r"^anonymously_chat-"),
                self.handle_link_chat,
            ),  # Handler for processing anonymous chat links
            MessageHandler(
                filters.TEXT & filters.Regex(r"^anonymously_msg-"), self.handle_link_msg
            ),  # Handler for processing anonymous message links
            CommandHandler(
                f"{self.leave_command}", self.leave_chat
            ),  # Handler for leaving a chat
            MessageHandler(
                filters.ALL
                & ~filters.COMMAND
                & ~filters.Regex(r"^anonymously_msg-")
                & ~filters.Regex(r"^anonymously_chat-")
                & ~filters.UpdateType.EDITED,
                self.reply_message,  # Handler for all non-command, non-link, non-edited messages (for chat forwarding)
            ),
            MessageHandler(
                filters.ALL & ~filters.COMMAND & filters.UpdateType.EDITED,
                self.handle_edit,  # Handler for edited messages
            ),
        ]
