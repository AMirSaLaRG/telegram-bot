import datetime
import logging
from telegram import (Update, InlineQueryResultArticle,
                      InputTextMessageContent, ReplyKeyboardMarkup,
                      KeyboardButton, InlineKeyboardButton,
                      InlineKeyboardMarkup, ReplyKeyboardRemove,)
from telegram.ext import (InlineQueryHandler, filters, ContextTypes, CommandHandler,
                          ApplicationBuilder, MessageHandler, CallbackQueryHandler,
                          ConversationHandler)
from data_base import UserDatabase



# Initialize DB
user_db = UserDatabase()



# todo last online time
class Profile:
    def __init__(self):
        self.PHOTO, self.NAME, self.AGE, self.GENDER, self.ABOUT, self.LOCATION = range(6)
        self.create_commend = 'createprofile'

    def get_profile_create_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler(self.create_commend, self.start_profile)],
            states={
                self.PHOTO: [MessageHandler(filters.PHOTO, self.handle_photo)],
                self.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name)],
                self.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_age)],
                self.GENDER: [MessageHandler(filters.Regex("^(Male|Female|Other)$"), self.handle_gender)],
                self.ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_about)],
                self.LOCATION: [MessageHandler(filters.LOCATION, self.handle_location)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

    # def save_profile(self, user_id: int, profile_data: dict):
    #     # Remove temporary file_id (we already saved the photo locally)
    #     if "profile_photo_file_id" in profile_data:
    #         del profile_data["profile_photo_file_id"]
    #
    #     # Load existing profiles
    #     try:
    #         with open("profiles/user_profiles.json", "r") as f:
    #             profiles = json.load(f)
    #     except FileNotFoundError:
    #         profiles = {}
    #
    #     # Update with new profile
    #     profiles[str(user_id)] = profile_data
    #
    #     # Save back to file
    #     with open("profiles/user_profiles.json", "w") as f:
    #         json.dump(profiles, f, indent=4)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Profile creation cancelled')
        return ConversationHandler.END

    async def start_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['user_id'] = update.effective_user.id
        await update.message.reply_text(
            "Lets create your profile.\n First send me your photo",
            reply_markup=ReplyKeyboardRemove()
        )
        return self.PHOTO

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # check photo
        if not update.message.photo:
            await update.message.reply_text("plz send your photo!")
            return self.PHOTO

        # store highest resolution
        photo_file = await update.message.photo[-1].get_file()
        context.user_data['profile_photo'] = photo_file.file_id
        print(context.user_data['profile_photo'])

        await update.message.reply_text("Great!! \n now send me your name")
        return self.NAME

    async def handle_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['name'] = update.message.text

        await update.message.reply_text("What's your age?")
        return self.AGE

    async def handle_age(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            age = int(update.message.text)
            if age < 13 or age > 120:
                raise ValueError
            context.user_data['age'] = age
        except ValueError:
            await update.message.reply_text("Please enter a valid age (13-120)")
            return self.AGE

        # Create gender selection keyboard
        reply_keyboard = [["Male"], ["Female"], ["Other"]]
        await update.message.reply_text(
            "Select your gender:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True,
                input_field_placeholder="Your gender?"
            )
        )
        return self.GENDER

    async def handle_gender(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['gender'] = update.message.text

        await update.message.reply_text(
            "Tell me something about yourself (max 200 characters):",
            reply_markup=ReplyKeyboardRemove()
        )
        return self.ABOUT

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(update.message.text) > 200:
            await update.message.reply_text("Please keep it under 200 characters!")
            return self.ABOUT

        context.user_data['about'] = update.message.text

        # Request location with a button
        reply_keyboard = [[KeyboardButton("Share Location", request_location=True)]]
        await update.message.reply_text(
            "Finally, share your location:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True
            )
        )
        return self.LOCATION

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        location = update.message.location
        context.user_data['location'] = (location.latitude, location.longitude)
        context.user_data['latitude'] = context.user_data['location'][0]
        context.user_data['longitude'] = context.user_data['location'][1]


        # Save the complete profile
        # self.save_profile(update.effective_user.id, context.user_data)
        user_db.add_or_update_user(update.effective_user.id ,context.user_data)

        # Display the profile
        await self.show_profile(update, context)

        return ConversationHandler.END

    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.load_profile(update, context)

        profile = context.user_data
        print(profile)
        text = (
            f"🏷 Name: {profile.get('name', 'Not set')}\n"
            f"🔢 Age: {profile.get('age', 'Not set')}\n"
            f"👤 Gender: {profile.get('gender', 'Not set')}\n"
            f"📝 About: {profile.get('about', 'Not set')}\n"
            f"📍 online: {profile.get('last_online', 'Not set')}"
        )

        if 'profile_photo' in profile:
            await update.message.reply_photo(
                photo=profile['profile_photo'],
                caption=text
            )
        else:
            await update.message.reply_text(text)

    def load_profile(sefl, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # user_id = str(update.effective_chat.id)
        #todo switch db
        user_db.add_or_update_user(update.effective_user.id, context.user_data)
        user_db.get_user_data(update.effective_user.id, context.user_data)


        # try:
        #     with open("profiles/user_profiles.json", 'r') as file:
        #         data = json.load(file)
        # except FileNotFoundError:
        #     print('file not created')
        # user_data = data[user_id]
        # context.user_data['profile_photo'] = user_data['profile_photo']
        # context.user_data['name'] = user_data['name']
        # context.user_data['age'] = user_data['age']
        # context.user_data['gender'] = user_data['gender']
        # context.user_data['about'] = user_data['about']
        # context.user_data['location'] = user_data['location']

    def check_exist_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['user_id'] = str(update.effective_chat.id)
        user_db.add_or_update_user(update.effective_user.id, context.user_data)
        try:
            context.user_data['name']
        except KeyError:
            return False
        else:
            if context.user_data['name'] == "":
                return False
            else:
                return True
        # try:
        #     with open("profiles/user_profiles.json", 'r') as file:
        #         data = json.load(file)
        #         if user_id in data:
        #             self.load_profile(update, context)
        #             return True
        #         else:
        #
        #             return False
        #
        # except FileNotFoundError:
        #     with open("profiles/user_profiles.json", 'w') as file:
        #         return False


class Calculator:
    def __init__(self):
        self.ITEM, self.AMOUNT, self.CONST_FEE, self.SHOP_FEE, self.TEXT = range(5)
        self.calculate_command = 'calculator'

    def get_calculated_price_conversation_handler(self):
        return ConversationHandler(
            entry_points=[
                CommandHandler(self.calculate_command, self.start_calculation),
                CallbackQueryHandler(self.start_calculation, pattern=f"^{self.calculate_command}$")
            ],
            states={
                self.ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_item)],
                self.AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_amount)],
                self.CONST_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_const_fee)],
                self.SHOP_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_shop_fee)],
                self.TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=True  # 👈 Add this line
        )
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Calculator stopped')
        return ConversationHandler.END

    async def start_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Handle both Message (command) and CallbackQuery (button) updates
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message
        await context.bot.send_message(
        chat_id=message.chat.id,
        text="Let's calculate it. \nFirst what item we will calculate",
        reply_markup=ReplyKeyboardRemove()
    )
        return self.ITEM

    async def handle_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        #check item
        if update.message.text != "18k":
            await update.message.reply_text("This item is not in our list plz Enter another:")
            return self.ITEM

        context.user_data['calculate_item'] = update.message.text

        await update.message.reply_text(f"OK! How much of {context.user_data['calculate_item']}:\n (gold: gram)")
        return self.AMOUNT
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            float(update.message.text)
        except ValueError:
            await update.message.reply_text(f"Plz enter the amount of {context.user_data['calculate_item']}\n gold: gram\nonly numbers")
            return self.AMOUNT
        else:
            context.user_data['amount'] = update.message.text

            await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
            return self.CONST_FEE

    async def handle_const_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            const_fee= float(update.message.text)
        except ValueError:
            await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
            return self.CONST_FEE
        else:
            if int(const_fee) not in range(100):
                await update.message.reply_text("Plz send contraction fee percentage: (1 to 100)")
                return self.CONST_FEE
            context.user_data['const_fee'] = update.message.text

            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE

    async def handle_shop_fee(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            shop_fee= float(update.message.text)
        except ValueError:
            await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
            return self.SHOP_FEE
        else:
            if int(shop_fee) not in range(100):
                await update.message.reply_text("Plz send shop fee percentage: (1 to 100)")
                return self.CONST_FEE
            context.user_data['shop_fee'] = update.message.text

            await update.message.reply_text("Plz send text percentage: (1 to 100)")
            return self.TEXT

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            shop_fee= float(update.message.text)
        except ValueError:
            await update.message.reply_text("Plz send text percentage: (1 to 100)")
            return self.TEXT
        else:
            if int(shop_fee) not in range(100):
                await update.message.reply_text("Plz send text percentage: (1 to 100)")
                return self.TEXT
            context.user_data['text'] = update.message.text


            await self.show_calculated_result(update, context)

            return ConversationHandler.END

    async def show_calculated_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (f"item : {context.user_data["calculate_item"]} "
                f"\n amount: {context.user_data['amount']}"
                f"\n construction fee: {context.user_data['const_fee']}%"
                f"\n shop fee: {context.user_data['shop_fee']}%"
                f"\n text: {context.user_data['text']}%")

        await update.message.reply_text(text)
