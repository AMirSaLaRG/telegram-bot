import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.database import UserDatabase
from bot.utils.messages import Messages


class ShowCases:
    def __init__(self):
        users_to_show = None
        self.user_db = UserDatabase()
        self.num_show_page = 10



    async def show_selected_users(self, query, context:ContextTypes.DEFAULT_TYPE, selected_users, current_page=1):
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
        all_pages = []
        page = ''
        context.user_data['current_page'] = current_page

        start_index = (current_page - 1) * self.num_show_page
        end_index = start_index + self.num_show_page
        paginated_users = selected_users[start_index:end_index]

        if not paginated_users and selected_users:
            context.user_data['current_page'] = 1
            start_index = 0
            end_index = self.num_show_page
            paginated_users = selected_users[start_index:end_index]

        for data in paginated_users:
            name = data['user'].name
            generated_id = data['user'].generated_id
            distance = int(data['distance'])

            if data['is_online']:
                last_online = Messages.ONLINE_ICON
            else:
                if int(data["mins_ago"]) <= 60:
                    last_online = f'{int(data["mins_ago"])} mins ago'
                elif int(data["mins_ago"]) <= 1440:
                    last_online = f'{int(int(data["mins_ago"]) / 60)} hr ago'
                elif int(data["mins_ago"]) <= 10080:
                    last_online = f'{int(int(data["mins_ago"]) / 1440)} day ago'
                else:
                    last_online = "long time ago"

            gender = data['user'].gender.lower()
            city = data['user'].city
            age = data['user'].age

            note = Messages.PROFILE_NOTE.format(
                gender_icon=Messages.MALE_ICON if gender == 'male' else Messages.FEMALE_ICON,
                name=name,
                age=age,
                last_online=last_online,
                city=city,
                distance=distance,
                generated_id=generated_id,
                divider=Messages.DIVIDER
            )
            page += note

        all_pages.append(page)
        total_pages = math.ceil(len(selected_users) / self.num_show_page)

        keyboard_buttons = []
        if total_pages > 1:
            if current_page > 1:
                keyboard_buttons.append(InlineKeyboardButton(Messages.BACK_BUTTON, callback_data='page_before'))
            if current_page < total_pages:
                keyboard_buttons.append(InlineKeyboardButton(Messages.NEXT_BUTTON, callback_data='page_next'))

        reply_markup = InlineKeyboardMarkup([keyboard_buttons]) if keyboard_buttons else None

        if paginated_users:
            # await query.edit_message_text(text=page, reply_markup=reply_markup)
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=page,
                reply_markup=reply_markup
            )
        else:
            # await query.edit_message_text(text=Messages.NO_PROFILES_FOUND)
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=Messages.NO_PROFILES_FOUND,

            )