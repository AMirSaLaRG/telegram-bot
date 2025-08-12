from telegram import Update
from telegram.ext import ContextTypes


from bot.handlers.intraction import track_user_interaction
from bot.db.database import RelationshipManager, UserDatabase
from bot.handlers.show_cases import ShowCases


from bot.utils.messages_manager import messages as msg

# messages = msg(language=context.user_data['lan'])


class RelationshipHandler:
    def __init__(self):
        self.rel_db = RelationshipManager()
        self.user_db = UserDatabase()
        self.show_case = ShowCases()
        messages = msg()
        self.rel_starter_pattern = messages.REL_STARTER_PATTERN
        self.rel_inspect_pattern = messages.REL_INSPECT_PATTERN
        self.like_pattern = messages.LIKE_PATTERN
        self.friend_pattern = messages.FRIEND_PATTERN
        self.block_pattern = messages.BLOCK_PATTERN
        self.report_pattern = messages.REPORT_PATTERN
        self.unlike_pattern = messages.UNLIKE_PATTERN
        self.unfriend_pattern = messages.UNFRIEND_PATTERN
        self.unblock_pattern = messages.UNBLOCK_PATTERN
        # self.unreport_pattern = Messages.REPORT_PATTERN

    async def buttons(self, update: Update, context):
        messages = msg(language=context.user_data["lan"])
        user_id = update.effective_user.id
        query = update.callback_query
        await query.answer()

        if query.data.startswith(self.rel_starter_pattern):
            action = query.data.split(":")[1].strip().lower()
            target_id = int(query.data.split(":")[2].strip().lower())

            if action == messages.LIKE_PATTERN:
                await self.liking_handler(update, context, target_id)
            if action == messages.FRIEND_PATTERN:
                await self.add_friend_handler(update, context, target_id)
            if action == messages.BLOCK_PATTERN:
                await self.block_handler(update, context, target_id)
            if action == messages.REPORT_PATTERN:
                await self.report_handler(update, context, target_id)

        if query.data.startswith(self.rel_inspect_pattern):
            action = query.data.split(":")[1].strip().lower()
            if action == self.like_pattern:
                await self.show_ppl(query, context, self._ppl_liked_me(user_id))
            if action == self.friend_pattern:
                await self.show_ppl(query, context, self._ppl_i_added(user_id))

    async def liking_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        user_id = update.effective_user.id
        self.rel_db.like(user_id, target_id)

    async def add_friend_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        query = update.callback_query
        success = self.rel_db.friend(query.from_user.id, target_id)
        if success:
            await query.answer("🤝 Friend request sent!", show_alert=True)
        else:
            await query.answer("⚠️ Could not add friend", show_alert=True)

    async def block_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        user_id = update.effective_user.id
        self.rel_db.block(user_id, target_id)

    async def report_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        user_id = update.effective_user.id
        self.rel_db.report(user_id, target_id)

    def unliking_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        user_id = update.effective_user.id
        self.rel_db.like(user_id, target_id, action=False)

    def unadd_friend_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        user_id = update.effective_user.id
        self.rel_db.friend(user_id, target_id, action=False)

    def unblock_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int
    ):
        user_id = update.effective_user.id
        self.rel_db.block(user_id, target_id, action=False)

    def _ppl_i_added(self, user_id: int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)["friends"]
        return []

    def _ppl_i_liked(self, user_id: int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)["likes"]
        return []

    def _ppl_liked_me(self, user_id: int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)["liked_by"]
        return []

    def _ppl_i_block(self, user_id: int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)["blocks"]
        return []

    async def show_ppl(self, query, context, the_users):
        the_users_id = [user.user_id for user in the_users]
        user_id = query.from_user.id
        all_users = self.user_db.get_users_apply_system_sorting_by_db(user_id)
        targets_users = [
            user for user in all_users if user["user"].user_id in the_users_id
        ]
        await self.show_case.show_selected_users(
            query, context, selected_users=targets_users
        )
