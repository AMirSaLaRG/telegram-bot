from datetime import datetime
import math

from dotenv import load_dotenv
import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQueryResultPhoto,
    InputMediaPhoto,
    Update,
)
from telegram.ext import ContextTypes

from bot.db.database import UserDatabase, User
from bot.utils.messages_manager import messages as msg

# messages = msg(language=context.user_data['lan'])
from bot.handlers.intraction import track_user_interaction

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")


class ShowCases:
    def __init__(self):
        self.user_db = UserDatabase()
        self.num_show_page = 5

    async def inline_show_selected_users(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        selected_users: list[dict[str, float | int | bool | User]],
        max_num: int = 50,
    ):
        """
        Handles inline queries to show user profiles in a scrollable interface.
        """

        user_id = update.inline_query.from_user.id

        # change later

        results = []

        for idx, user_data in enumerate(selected_users[:max_num]):
            user = user_data["user"]
            try:
                distance = int(user_data["distance"])
            except ValueError:
                distance = 'xXx'
            is_online = user_data["is_online"]

            # Format profile information
            if is_online:
                status = "🟢 Online"
            else:
                mins_ago = int(user_data["mins_ago"])
                if mins_ago < 60:
                    status = f"⏱ {mins_ago} mins ago"
                else:
                    status = f"⏱ {mins_ago // 60} hours ago"

            caption = f"/chaT_{user.generated_id}"
            # print(user_data, is_online, status)

            # Create inline result - using Article if no photo, Photo if available
            if user.profile_photo:
                file = await context.bot.get_file(user.profile_photo)
                photo_url = file.file_path
            else:
                photo_url = None
            results.append(
                InlineQueryResultArticle(
                    id=str(idx),
                    title=f"{user.name} ({user.age})",
                    description=f"{user.city} | {distance}km | {status}",
                    thumbnail_url=photo_url,  # Use file_id directly
                    thumbnail_width=100,
                    thumbnail_height=100,
                    input_message_content=InputTextMessageContent(
                        caption, disable_web_page_preview=True
                    ),
                )
            )

            # else:
            #     pass
            #     # results.append(
            #     #     InlineQueryResultArticle(
            #     #         id=str(idx),
            #     #         title=f"{user.name} ({user.age})",
            #     #         description=f"{user.city} | {distance}km | {status}",
            #     #         input_message_content=InputTextMessageContent(
            #     #             caption,
            #     #             disable_web_page_preview=True
            #     #         )
            #     #     )
            #     # )

        await update.inline_query.answer(results, cache_time=0)

    async def show_selected_users(
        self,
        query,
        context: ContextTypes.DEFAULT_TYPE,
        selected_users=None,
        current_page=1,
        title="",
    ):
        """
        Handles user search requests by applying filters and displaying matching profiles.

        Processes user search criteria from context, queries the database for matches,
        and formats the results into a paginated message with profile previews.

        Features:
        - Online status detection ('Online' or time-based last seen)
        - Distance display in kilometers
        - Profile linking via /chaT_[id] commands
        - Automatic filter reset after search

        Args:
            query: Telegram callback query object
            context: Context object containing user data and filters
            current_page: shows the number of page it shows starts from one default
            selected_users: ppl to show
        Returns:
            None (edits the original message with results)

        Side Effects:
            - Updates user data if no generated_id exists
            - Resets user_filter in context after search
            - Modifies the original query message
        """
        messages = msg(language=context.user_data["lan"])
        all_pages = []
        time = datetime.now().strftime("%m/%d/%Y, %H:%M")
        title = title
        header = f"{title}\n {time}"
        page = f"{header}\n\n"
        context.user_data["current_page"] = current_page

        if selected_users is not None:
            context.user_data["selected_users"] = selected_users
            first_time = True
        else:
            selected_users = context.user_data.get("selected_users", [])
            first_time = False
        start_index = (current_page - 1) * self.num_show_page
        end_index = start_index + self.num_show_page
        paginated_users = selected_users[start_index:end_index]

        if not paginated_users and selected_users:
            context.user_data["current_page"] = 1
            start_index = 0
            end_index = self.num_show_page
            paginated_users = selected_users[start_index:end_index]

        for data in paginated_users:
            name = data["user"].name
            generated_id = data["user"].generated_id
            try:
                distance = int(data["distance"])
            except ValueError:
                distance = 'xXx'

            if data["is_online"]:
                last_online = messages.ONLINE_ICON
            else:
                if int(data["mins_ago"]) <= 60:
                    last_online = f"{int(data['mins_ago'])} mins ago"
                elif int(data["mins_ago"]) <= 1440:
                    last_online = f"{int(int(data['mins_ago']) / 60)} hr ago"
                elif int(data["mins_ago"]) <= 10080:
                    last_online = f"{int(int(data['mins_ago']) / 1440)} day ago"
                else:
                    last_online = "long time ago"

            gender = data["user"].gender.lower()
            city = data["user"].city
            age = data["user"].age

            note = messages.PROFILE_NOTE.format(
                gender_icon=(
                    messages.MALE_ICON if gender == "male" else messages.FEMALE_ICON
                ),
                name=name,
                age=age,
                last_online=last_online,
                city=city,
                distance=distance,
                generated_id=generated_id,
                divider=messages.DIVIDER,
            )
            page += note

        all_pages.append(page)
        total_pages = math.ceil(len(selected_users) / self.num_show_page)

        keyboard_buttons = [
            InlineKeyboardButton(
                "look Inline mode",
                switch_inline_query_current_chat=messages.QUERY_PATTERN_FILTERED_PPL,
            )
        ]
        if total_pages > 1:
            if current_page > 1:
                keyboard_buttons.append(
                    InlineKeyboardButton(
                        messages.BACK_BUTTON, callback_data="page_before"
                    )
                )
            if current_page < total_pages:
                keyboard_buttons.append(
                    InlineKeyboardButton(
                        messages.NEXT_BUTTON, callback_data="page_next"
                    )
                )

        reply_markup = (
            InlineKeyboardMarkup([keyboard_buttons]) if keyboard_buttons else None
        )

        if first_time:
            if paginated_users:
                # await query.edit_message_text(text=page, reply_markup=reply_markup)
                await context.bot.send_message(
                    chat_id=query.message.chat.id, text=page, reply_markup=reply_markup
                )
            else:
                # await query.edit_message_text(text=Messages.NO_PROFILES_FOUND)
                await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text=messages.NO_PROFILES_FOUND,
                )
        else:
            if paginated_users:
                # await query.edit_message_text(text=page, reply_markup=reply_markup)
                await query.edit_message_text(text=page, reply_markup=reply_markup)

    async def buttons(self, update, context):
        query = update.callback_query
        await query.answer()

        if query.data == "page_before":
            await self.show_selected_users(
                query,
                context,
                current_page=context.user_data.get("current_page", 1) - 1,
            )
        elif query.data == "page_next":
            await self.show_selected_users(
                query,
                context,
                current_page=context.user_data.get("current_page", 1) + 1,
            )
