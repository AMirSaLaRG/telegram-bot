from telegram import Update
from telegram.ext import ContextTypes



from bot.handlers.intraction import track_user_interaction
from bot.db.database import RelationshipManager, UserDatabase
from bot.handlers.show_cases import ShowCases


from bot.utils.messages import Messages



class RelationshipHandler:
    def __init__(self):
        self.rel_db = RelationshipManager()
        self.user_db = UserDatabase()
        self.show_case = ShowCases()
        self.rel_starter_pattern = Messages.REL_STARTER_PATTERN
        self.rel_inspect_pattern = Messages.REL_INSPECT_PATTERN
        self.like_pattern = Messages.LIKE_PATTERN
        self.friend_pattern = Messages.FRIEND_PATTERN
        self.block_pattern = Messages.BLOCK_PATTERN
        self.report_pattern = Messages.REPORT_PATTERN
        self.unlike_pattern = Messages.UNLIKE_PATTERN
        self.unfriend_pattern = Messages.UNFRIEND_PATTERN
        self.unblock_pattern = Messages.UNBLOCK_PATTERN
        # self.unreport_pattern = Messages.REPORT_PATTERN

    @track_user_interaction
    async def buttons(self, update:Update, context):
        user_id = update.effective_user.id
        query = update.callback_query
        await query.answer()

        # if query.data.startswith(self.rel_starter_pattern):
        #     action = query.data.split(':')[1].strip().lower()
        #     target_id = int(query.data.split(':')[2].strip().lower())
        #
        #     if action == Messages.LIKE_PATTERN:
        #         self.liking_handler(update, context, target_id)
        #     if action == Messages.FRIEND_PATTERN:
        #         self.add_friend_handler(update, context, target_id)
        #     if action == Messages.BLOCK_PATTERN:
        #         self.block_handler(update, context, target_id)
        #     if action == Messages.REPORT_PATTERN:
        #         self.report_handler(update, context, target_id)


        if query.data.startswith(self.rel_inspect_pattern):
            action = query.data.split(':')[1].strip().lower()
            if action == self.like_pattern:
                await self.show_ppl(query, context, self._ppl_i_liked(user_id))
            if action == self.friend_pattern:
                await self.show_ppl(query, context, self._ppl_i_added(user_id))





    def liking_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.like(user_id, target_id)

    def add_friend_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.friend(user_id, target_id)

    def block_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.block(user_id, target_id)

    def report_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.report(user_id, target_id)

    def unliking_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.like(user_id, target_id, action=False)

    def unadd_friend_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.friend(user_id, target_id, action=False)

    def unblock_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
        user_id = update.effective_user.id
        self.rel_db.block(user_id, target_id, action=False)


    def _ppl_i_added(self, user_id:int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)['friends']
        return []
    def _ppl_i_liked(self, user_id:int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)['likes']
        return []

    def _ppl_i_block(self, user_id:int):
        if self.rel_db.get_user_relationships(user_id):
            return self.rel_db.get_user_relationships(user_id)['blocks']
        return []

    async def show_ppl(self,query, context, the_users):
        the_users_id = [user.user_id for user in the_users]
        user_id = query.from_user.id
        all_users = self.user_db.get_users_apply_system_sorting_by_db(user_id)
        targets_users = [user for user in all_users if user['user'].user_id in the_users_id]
        await self.show_case.show_selected_users(query, context, targets_users)