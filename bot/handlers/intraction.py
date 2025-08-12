from telegram.ext import ContextTypes
from telegram import Update
from bot.db.database import ChatDatabase, UserDatabase
from datetime import datetime
from functools import wraps
import logging
from bot.utils.messages_manager import languages as lans

# Set up logging
logger = logging.getLogger(__name__)  # This creates a logger with your module's name
logger.setLevel(logging.DEBUG)  # Set the minimum log level to capture

# Create console handler and set level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
logger.addHandler(ch)

chat_db = ChatDatabase()
user_db = UserDatabase()


async def interact(update_query, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler activates for almost any user interaction.
    It ensures the user's session exists and updates their last_online status.
    """
    try:
        if hasattr(update_query, "effective_user"):
            user_id = update_query.effective_user.id

        elif hasattr(update_query, "from_user"):
            user_id = update_query.from_user.id
        else:
            print("what is going on in interact")
            user_id = ""

        chat_db.create_user_session(user_id)
        context.user_data["user_id"] = user_id
        context.user_data["last_online"] = datetime.now()
        user_db.add_or_update_user(user_id, context.user_data)
    except Exception as e:
        print(f"Could not update the user: {e}")


# as decorator
def track_user_interaction(func):
    """
    Decorator that works for both standalone functions and class methods.
    Handles user interaction tracking for Telegram bot handlers.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Determine if this is a class method or standalone function
        if len(args) >= 2 and isinstance(args[1], Update):
            # Class method case (self, update, context)
            update = args[1]
            context = args[2] if len(args) > 2 else kwargs.get("context")
        else:
            # Standalone function case (update, context)
            update = args[0] if args else kwargs.get("update")
            context = args[1] if len(args) > 1 else kwargs.get("context")

        if not update or not context:
            logger.warning("Couldn't extract update and context from arguments")
            return await func(*args, **kwargs)

        try:
            user = None
            if hasattr(update, "effective_user"):
                user = update.effective_user
            elif hasattr(update, "from_user"):
                user = update.from_user

            if user:
                user_id = user.id
                chat_db.create_user_session(user_id)
                context.user_data["user_id"] = user_id
                context.user_data["last_online"] = datetime.now()
                language = context.user_data.get("lan", None)
                print(language)
                if not language in [lan for lan, value in lans.items()]:
                    print("yay")
                    context.user_data["language"] = [
                        lan for lan, value in lans.items()
                    ][0]
                    context.user_data["lan"] = [lan for lan, value in lans.items()][0]
                user_db.add_or_update_user(user_id, context.user_data)
                logger.debug(f"Tracked interaction for user {user_id}")

            print(context.user_data)
        except Exception as e:
            logger.error(f"Error in user tracking: {e}", exc_info=True)

        return await func(*args, **kwargs)

    return wrapper
