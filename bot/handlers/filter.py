import math
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.db.database import iran_cities_fa
from bot.handlers.intraction import track_user_interaction
from bot.db.database import UserDatabase
from bot.handlers.show_cases import ShowCases

from bot.utils.messages_manager import messages as msg
# messages = msg(language=context.user_data['lan'])




class Filter:
    def __init__(self):
        self.user_db = UserDatabase()
        self.show_cases = ShowCases()

    @track_user_interaction
    async def advance_search(self, update: Update, context:
    ContextTypes.DEFAULT_TYPE):
        """
        Initiates the advanced search filter selection.
        Presents inline buttons for various filtering options (Distance, Last Online, Gender, Age, Cities).
        """
        messages = msg(language=context.user_data['lan'])
        keyboard = [
            [
                InlineKeyboardButton(messages.DISTANCE_FILTER, callback_data='A_F: Dis'),
                InlineKeyboardButton(messages.LAST_ONLINE_FILTER, callback_data='A_F: last_online')
            ],
            [
                InlineKeyboardButton(messages.GENDER_FILTER, callback_data='A_F: Gender'),
                InlineKeyboardButton(messages.AGE_FILTER, callback_data='A_F: Age')
            ],
            [InlineKeyboardButton(messages.CITIES_FILTER, callback_data='A_F: Cities')],
            [InlineKeyboardButton(messages.SEARCH_BUTTON, callback_data='A_F: Search')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=messages.ADVANCE_SEARCH_TITLE,
            reply_markup=reply_markup
        )

    def advance_search_handler(self):
        messages = msg()
        return MessageHandler(filters.Regex(messages.ADVANCE_SEARCH_REGEX), self.advance_search)


    async def buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data.startswith('A_F:'):
            if 'user_filter' not in context.user_data:
                context.user_data['user_filter'] = {}
            filter_name = query.data.split(':')[1].strip().lower()
            await self.advance_filter_lvl1_buttons(query, context, filter_name)
        elif query.data.startswith('A_F_D'):
            await self.advance_filter_lvl2_buttons(query, context)
        elif query.data.startswith("gender:"):
            await self.gender_filter_buttons(query, context)
        elif query.data.startswith("random gender:"):
            await self.random_search_gender_filter_buttons(query, context)

        elif query.data.startswith("age_filter:"):
            await self.age_filter_buttons(query, context)
        elif query.data.startswith("city_filter:"):
            await self.city_filter_buttons(query, context)




    async def advance_filter_lvl1_buttons(self, query, context: ContextTypes.DEFAULT_TYPE, filter_name):
        """
        handles advance filter inline buttons
        """

        if filter_name == "dis":
            await self.distance_filter_handler(query, context)
        if filter_name == 'last_online':
            await self.last_online_filter_handler(query, context)
        if filter_name == 'gender':
            await self.gender_filter_handler(query, context)
        if filter_name == 'age':
            await self.age_filter_handler(query, context)
        if filter_name == 'cities':
            await self.cities_filter_handler(query, context)
        if filter_name == 'search':
            await self.search_filters_handler(query, context)

    async def advance_filter_lvl2_buttons(self, query, context: ContextTypes.DEFAULT_TYPE):
        """
        handles advance filter inline buttons
        :return: functioning button
        """

        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if query.data.startswith('A_F_D: dis_filter:'):
            self.get_dis_filter(query, context)
        if query.data.startswith("A_F_D: last_online_filter:"):
            self.get_last_online_filter(query, context)
        if query.data.startswith("A_F_D: gender: done"):
            self.get_gender_filter(query, context)
        await self.update_advance_search(query, context)

    async def gender_filter_buttons(self, query, context: ContextTypes.DEFAULT_TYPE):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "gender_filter" not in context.user_data:
            context.user_data['gender_filter'] = []

        gender_filter = context.user_data['gender_filter']
        action = query.data.split(":")[1].strip().lower()

        if action in ["male", "female"]:
            if action in gender_filter:
                gender_filter.remove(action)
            else:
                gender_filter.append(action)
            await self.gender_filter_handler(query, context)

    async def random_search_gender_filter_buttons(self, query, context: ContextTypes.DEFAULT_TYPE):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "gender_filter" not in context.user_data:
            context.user_data['gender_filter'] = []

        gender_filter = context.user_data['gender_filter']
        action = query.data.split(":")[1].strip().lower()

        if action in ["male", "female"]:
            if action in gender_filter:
                gender_filter.remove(action)
            else:
                gender_filter.append(action)
            await self.random_chat_gender_done(query, context)

    async def age_filter_buttons(self, query, context: ContextTypes.DEFAULT_TYPE):
        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "age_filter" not in context.user_data['user_filter']:
            context.user_data['user_filter']['age_filter'] = []

        age_filter = context.user_data['user_filter']['age_filter']
        action = int(query.data.split(':')[1].strip())

        if action in age_filter:
            age_filter.remove(action)
        else:
            age_filter.append(action)
        await self.age_filter_handler(query, context)

    async def city_filter_buttons(self, query, context: ContextTypes.DEFAULT_TYPE):

        if 'user_filter' not in context.user_data:
            context.user_data['user_filter'] = {}
        if "city_filter" not in context.user_data['user_filter']:
            context.user_data['city_filter'] = []

        city_filter = context.user_data['user_filter']['city_filter']
        action = query.data.split(":")[1].strip().lower()

        if action == "all":
            if len(city_filter) == len(iran_cities_fa):
                city_filter.clear()
            else:
                city_filter.clear()
                for city in iran_cities_fa:
                    city_filter.append(city)
        elif action in city_filter:
            city_filter.remove(action)
        else:
            city_filter.append(action)
        await self.cities_filter_handler(query, context)

    async def distance_filter_handler(self, query, context):
        """
        Displays inline keyboard for distance filtering options in advanced search.
        """
        messages = msg(language=context.user_data['lan'])
        keyboard = [
            [
                InlineKeyboardButton(messages.DISTANCE_5KM, callback_data='A_F_D: dis_filter: 5km'),
                InlineKeyboardButton(messages.DISTANCE_10KM, callback_data='A_F_D: dis_filter: 10km'),
            ],
            [
                InlineKeyboardButton(messages.DISTANCE_15KM, callback_data='A_F_D: dis_filter: 15km'),
                InlineKeyboardButton(messages.DISTANCE_20KM, callback_data='A_F_D: dis_filter: 20km'),
            ],
            [
                InlineKeyboardButton(messages.DISTANCE_25KM, callback_data='A_F_D: dis_filter: 25km'),
                InlineKeyboardButton(messages.DISTANCE_30KM, callback_data='A_F_D: dis_filter: 30km'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(messages.CHOOSE_PROMPT, reply_markup=reply_markup)

    def get_dis_filter(self, query, context):
        """
        Extracts the selected distance filter from the callback query and stores it in user_data.
        """
        dis_filter = query.data.split(':')[2].strip().lower().split('km')[0]
        context.user_data['user_filter']['dis_filter'] = int(dis_filter)

    async def last_online_filter_handler(self, query, context):
        """
        Displays inline keyboard for 'last online' filtering options in advanced search.
        """
        messages = msg(language=context.user_data['lan'])
        keyboard = [
            [
                InlineKeyboardButton(messages.TIME_15MIN, callback_data='A_F_D: last_online_filter: 15min'),
                InlineKeyboardButton(messages.TIME_30MIN, callback_data='A_F_D: last_online_filter: 30min'),
            ],
            [
                InlineKeyboardButton(messages.TIME_1HR, callback_data='A_F_D: last_online_filter: 1hr'),
                InlineKeyboardButton(messages.TIME_3HR, callback_data='A_F_D: last_online_filter: 3hr'),
            ],
            [
                InlineKeyboardButton(messages.TIME_1DAY, callback_data='A_F_D: last_online_filter: 1day'),
                InlineKeyboardButton(messages.TIME_1WEEK, callback_data='A_F_D: last_online_filter: 1week'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(messages.CHOOSE_PROMPT, reply_markup=reply_markup)

    def get_last_online_filter(self, query, context):
        """
        Extracts the selected 'last online' filter from the callback query and stores it in user_data.
        Converts time strings (e.g., '15min') to minutes.
        """
        global dict_last_online
        dict_last_online = {
            "15min": 15,
            "30min": 30,
            "1hr": 60,
            "3hr": 180,
            "1day": 1440,
            "1week": 1080,
        }
        last_online_filter_full = query.data.split(':')[2].strip().lower()
        last_online_filter = dict_last_online[last_online_filter_full]
        context.user_data['user_filter']['last_online_filter'] = last_online_filter

    async def gender_filter_handler(self, query, context):
        """
        Displays inline keyboard for gender filtering in advanced search, with current selections marked.
        Toggles selection of 'male' or 'female'.
        """
        messages = msg(language=context.user_data['lan'])
        if "gender_filter" not in context.user_data:
            context.user_data['gender_filter'] = []

        gender_filter = context.user_data['gender_filter']
        keyboard = [
            [
                InlineKeyboardButton(f"{'✓ ' if 'male' in gender_filter else ''}{messages.MALE_OPTION}",
                                     callback_data="gender: male"),
                InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}{messages.FEMALE_OPTION}",
                                     callback_data="gender: female"),
            ],
            [InlineKeyboardButton(messages.DONE_BUTTON, callback_data="A_F_D: gender: done")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=messages.CHOOSE_GENDER,
            reply_markup=reply_markup,
        )

    async def random_chat_gender_done(self, query, context):
        """
        Updates the gender filter options for random chat, similar to the general gender filter handler.
        """
        messages = msg(language=context.user_data['lan'])
        if "gender_filter" not in context.user_data:
            context.user_data['gender_filter'] = []

        gender_filter = context.user_data['gender_filter']
        keyboard = [
            [
                InlineKeyboardButton(f"{'✓ ' if 'male' in gender_filter else ''}{messages.MALE_OPTION}",
                                     callback_data="random gender: male"),
                InlineKeyboardButton(f"{'✓ ' if 'female' in gender_filter else ''}{messages.FEMALE_OPTION}",
                                     callback_data="random gender: female"),
            ],
            [InlineKeyboardButton(messages.DONE_BUTTON, callback_data="random_chat: gender: done")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=messages.CHOOSE_GENDER,
            reply_markup=reply_markup,
        )

    def get_gender_filter(self, query, context):
        """
        Stores the selected gender filter into the 'user_filter' dictionary within user_data.
        """
        context.user_data['user_filter']['gender_filter'] = context.user_data['gender_filter']

    async def age_filter_handler(self, query, context, i=None):
        """
        Displays inline keyboard for age filtering in advanced search.
        Allows selection of one or two age values to define a range.
        Handles dynamic display of selected ages.
        """
        messages = msg(language=context.user_data['lan'])
        if "user_filter" not in context.user_data:
            context.user_data['user_filter'] = {}
        if "age_filter" not in context.user_data['user_filter']:
            context.user_data['user_filter']['age_filter'] = []

        if len(context.user_data['user_filter']['age_filter']) > 2:
            context.user_data['user_filter']['age_filter'].sort()
            a = context.user_data['user_filter']['age_filter'][0]
            b = context.user_data['user_filter']['age_filter'][-1]
            context.user_data['user_filter']['age_filter'].clear()
            context.user_data['user_filter']['age_filter'] = [a, b]

        age_filter = context.user_data['user_filter']['age_filter']

        if len(age_filter) == 2:
            keyboard = [
                           [
                               InlineKeyboardButton(
                                   f"{'✓ ' if (8 * i + n) + 1 in range(age_filter[0], age_filter[1] + 1) else ''}{(8 * i + n) + 1}",
                                   callback_data=f'age_filter: {(8 * i + n) + 1}') for n in range(8)
                           ] for i in range(1, 13)
                       ] + [[InlineKeyboardButton(messages.DONE_BUTTON, callback_data="A_F_D: age: done")]]
        else:
            keyboard = [
                           [
                               InlineKeyboardButton(f"{'✓ ' if (8 * i + n) + 1 in age_filter else ''}{(8 * i + n) + 1}",
                                                    callback_data=f'age_filter: {(8 * i + n) + 1}') for n in range(8)
                           ] for i in range(1, 13)
                       ] + [[InlineKeyboardButton(messages.DONE_BUTTON, callback_data="A_F_D: age: done")]]

        if len(context.user_data['user_filter']['age_filter']) == 2:
            context.user_data['user_filter']['age_filter'].sort()
            text = f'from: {context.user_data["user_filter"]["age_filter"][0]} to: {context.user_data["user_filter"]["age_filter"][1]}'
        elif len(context.user_data['user_filter']['age_filter']) == 1:
            text = f'-{context.user_data["user_filter"]["age_filter"][0]}-'
        else:
            text = messages.CHOOSE_STARTING_AGE

        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

    async def cities_filter_handler(self, query, context):
        """
        Displays inline keyboard for city filtering in advanced search, with current selections marked.
        Allows toggling individual cities or selecting/deselecting all cities.
        """
        messages = msg(language=context.user_data['lan'])
        if "city_filter" not in context.user_data['user_filter']:
            context.user_data['user_filter']['city_filter'] = []

        city_filter = context.user_data['user_filter']['city_filter']
        keyboard = [
                       [
                           InlineKeyboardButton(f"{'✓ ' if city in city_filter else ''}{city}",
                                                callback_data=f'city_filter: {city}') for city
                           in iran_cities_fa[i * 4: (i * 4) + 4]
                       ] for i in range(10)
                   ] + [
                       [
                           InlineKeyboardButton(messages.ALL_BUTTON, callback_data="city_filter: all"),
                           InlineKeyboardButton(messages.DONE_BUTTON, callback_data="A_F_D: city: done"),
                       ],
                   ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(messages.CHOOSE_PROMPT, reply_markup=reply_markup)

    def apply_dis_filter(self, user_filters, selected_users):
        """
        filters by distance
        :param user_filters: the filters that saved inside user_data
        :param selected_users: the users
        :return: list of who passed the filter
        """
        dis_filter = user_filters.get('dis_filter', None)

        if user_filters:
            if dis_filter:
                max_dis = float(user_filters['dis_filter'])
                return [u for u in selected_users if u['distance'] <= max_dis]

        return selected_users

    def apply_last_online_filter(self, user_filters, selected_users):
        """
        filters by last_online
        :param user_filters: the filters that saved inside user_data
        :param selected_users: the users
        :return: list of who passed the filter
        """
        last_online = user_filters.get('last_online_filter', None)
        if user_filters:
            if last_online:
                max_mins = int(user_filters['last_online_filter'])
                return [u for u in selected_users if u['mins_ago'] <= max_mins]

        return selected_users

    def apply_gender_filter(self, user_filters, selected_users):
        """
        filters by gender
        :param user_filters: the filters that saved inside user_data
        :param selected_users: the users
        :return: list of who passed the filter
        """
        gender_filter = user_filters.get('gender_filter', None)

        if user_filters:
            if gender_filter:
                gender_filter = [g.lower() for g in user_filters['gender_filter']]
                return [
                    u for u in selected_users
                    if u['user'].gender and u['user'].gender.lower() in gender_filter
                ]

        return selected_users

    def apply_age_filter(self, user_filters, selected_users):
        """
        filters by age
        :param user_filters: the filters that saved inside user_data
        :param selected_users: the users
        :return: list of who passed the filter
        """
        age_filter = user_filters.get('age_filter', None)
        if user_filters:
            if age_filter:
                age_filter = user_filters['age_filter']
                if len(age_filter) == 2:  # Age range [min, max]
                    min_age, max_age = age_filter
                    return [
                        u for u in selected_users
                        if u['user'].age is not None and min_age <= u['user'].age <= max_age
                    ]
                elif len(age_filter) == 1:  # Exact age
                    return [
                        u for u in selected_users
                        if u['user'].age is not None and u['user'].age == age_filter[0]
                    ]

        return selected_users



    def apply_city_filter(self, user_filters, selected_users) :
        """
        filters by city
        :param user_filters: the filters that saved inside user_data
        :param selected_users: the users
        :return: list of who passed the filter
        """
        city_filter = user_filters.get('city_filter', None)
        if user_filters:
            if city_filter:
                city_filter = user_filters['city_filter']
                return [
                    u for u in selected_users
                    if u['user'].city and u['user'].city in city_filter
                ]

        return selected_users

    def get_filtered_users(self, user_data: dict) -> List[dict]:
        """
        Returns a list of filtered users based on various criteria provided in `user_data`.
        The criteria can include distance, last online time, gender, age, and city.

        Args:
            user_data (dict): A dictionary containing user_id and 'user_filter' criteria.
                - 'user_id' (int): The ID of the requesting user.
                - 'user_filter' (dict, optional): Dictionary of filter criteria:
                    - 'dis_filter' (float, optional): Max distance in km.
                    - 'last_online_filter' (int, optional): Max minutes since last online.
                    - 'gender_filter' (list[str], optional): List of genders to include (e.g., ["male", "female"]).
                    - 'age_filter' (list[int], optional): [min_age, max_age] or [exact_age].
                    - 'city_filter' (list[str], optional): List of cities to include.

        Returns:
            List[dict]: Each dictionary contains user data with 'user' object,
                        'distance', 'mins_ago', and 'is_online' status.
                        Returns an empty list if no users match the criteria or on error.
        """
        try:
            user_id = int(user_data.get('user_id', ""))
            self.user_db.add_or_update_user(user_id, user_data)
            self.user_db.get_user_data(user_id, user_data)

            user_filters = user_data.get('user_filter', {})
            selected_users = self.user_db.get_users_apply_system_sorting_by_db(int(user_id))
            if not selected_users:
                return []

            selected_users = self.apply_dis_filter(user_filters, selected_users)
            selected_users = self.apply_last_online_filter(user_filters, selected_users)
            selected_users = self.apply_gender_filter(user_filters, selected_users)
            selected_users = self.apply_age_filter(user_filters, selected_users)
            selected_users = self.apply_city_filter(user_filters, selected_users)

            return selected_users
        except Exception as e:
            print(f'in applying filter Error : {e}')
            return []

    async def search_filters_handler(self, query, context):
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

            Returns:
                None (edits the original message with results)

            Side Effects:
                - Updates user data if no generated_id exists
                - Resets user_filter in context after search
                - Modifies the original query message
            """
        user_id = query.from_user.id
        generated_id = context.user_data.get('generated_id')

        if not generated_id:
            self.user_db.add_or_update_user(user_id, context.user_data)
        user_data = getattr(context, 'user_data', {})



        selected_users = self.get_filtered_users(user_data)
        #reset user filter
        context.user_data['user_filter'] = {}
        context.user_data['gender_filter'] = []




        await self.show_cases.show_selected_users(query, context, selected_users=selected_users)

    async def update_advance_search(self, query, context: ContextTypes.DEFAULT_TYPE):
        """
        Updates the displayed advanced search message with the currently applied filters.
        Reflects selections for distance, last online, gender, age, and cities on the buttons.
        """
        messages = msg(language=context.user_data['lan'])
        filter_data = context.user_data['user_filter']

        dis = f": {filter_data['dis_filter']}km" if "dis_filter" in filter_data else ""

        if "last_online_filter" in filter_data:
            reverse_dict = {v: k for k, v in dict_last_online.items()}
            last_online = f"{reverse_dict[filter_data['last_online_filter']]}"
        else:
            last_online = ""

        if "gender_filter" in filter_data:
            gender = ", ".join(filter_data["gender_filter"])
        else:
            gender = ""

        if "age_filter" in filter_data:
            if len(filter_data['age_filter']) == 1:
                age = f": {filter_data['age_filter'][0]}"
            elif len(filter_data['age_filter']) == 2:
                age = f": {filter_data['age_filter'][0]} to {filter_data['age_filter'][1]}"
            else:
                age = ""
        else:
            age = ""

        num_cities = f": {len(filter_data['city_filter'])}" if "city_filter" in filter_data else ""

        keyboard = [
            [
                InlineKeyboardButton(f"{messages.DISTANCE_FILTER}{dis}", callback_data='A_F: Dis'),
                InlineKeyboardButton(f"{messages.LAST_ONLINE_FILTER}{last_online}", callback_data='A_F: last_online')
            ],
            [
                InlineKeyboardButton(f"{gender if gender else messages.GENDER_FILTER}", callback_data='A_F: Gender'),
                InlineKeyboardButton(f"{messages.AGE_FILTER}{age}", callback_data='A_F: Age')
            ],
            [InlineKeyboardButton(f"{messages.CITIES_FILTER}{num_cities}", callback_data='A_F: Cities')],
            [InlineKeyboardButton(messages.SEARCH_BUTTON, callback_data='A_F: Search')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=messages.ADVANCE_SEARCH_TITLE,
            reply_markup=reply_markup
        )
