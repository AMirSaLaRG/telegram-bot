class Messages:
    # ==============================================
    # Frequently Changing Messages (Top)
    # ==============================================
    TOROB_EDIT_PRICE = "Edit Price"
    TOROB_EDIT_URL = "Edit URL"
    TOROB_EDIT_NAME = "Edit Name"
    TOROB_EDIT_DELETE = "delete"

    EDIT_BUTTON = "Edit"

    LIKES_SHOW_BUTTON = "Likes"
    FRIENDS_SHOW_BUTTON = "Friends"

    EDIT_NAME_BUTTON = "Edit Name"
    EDIT_ABOUT_BUTTON = "Edit About"
    EDIT_CITY_BUTTON = "Edit City"
    EDIT_LOCATION_BUTTON = "Edit Location"
    EDIT_LANGUAGE_BUTTON = "Edit Language"
    EDIT_PHOTO_BUTTON = "Update Photo"

    EDIT_NAME_TEXT = "Please enter your new name:"
    EDIT_ABOUT_TEXT = "Please enter your new bio/about text:"
    EDIT_CITY_TEXT = "Please enter your new city:"
    EDIT_LOCATION_TEXT = "Please send your location"
    EDIT_LANGUAGE_TEXT = "Plz choose your language:"
    EDIT_PHOTO_TEXT = "Please send your new profile photo:"

    EDIT_PHOTO_VALIDATION_ERROR = "Please send a valid photo"
    EDIT_PHOTO_SUCCESS = "Profile photo updated!"
    EDIT_PHOTO_CANCELED = "Profile editing cancelled"

    EDIT_LOCATION_SUCCESS = "Location updated"

    EDIT_CITY_SUCCESS = "City updated to: {new_city}"

    EDIT_ABOUT_ERROR_LONG = "Bio is too long, please shorten it"
    EDIT_ABOUT_SUCCESS = "Bio updated successfully!"

    EDIT_NAME_SUCCESS = "Name updated to: {new_name}"

    # General messages
    START_MESSAGE = "start"
    WHAT_YOU_LOOKING_FOR = "What you looking for?"
    ADVANCE_SEARCH_TITLE = "advance searched:"
    RANDOM_CHAT_PROMPT = "random_chat mikhai"
    CHOOSE_PROMPT = "Chose"
    CHOOSE_GENDER = "Chose gender:"
    CHOOSE_STARTING_AGE = "plz chose starting age:"
    NO_PROFILES_FOUND = "Could not find any profile for this filter\n\n/start"
    NOTHING_TO_SHOW = "there is nothing to show plz add some \n\n /start"
    ITEM_ON_EDIT_MODE = "✅ Item On Edit Mode!\n\nItem: {name}\nCurrent Highest Price: {price}\n\nCurrent URL: {url}\n\nWhat would you like to edit?"

    # Error messages
    INVALID_FORMAT = "invalid format. use/{command}_<something>"
    INVALID_ITEM = "invalid item. Could not find this item"
    USER_NOT_REGISTERED = "This user is not registered!"
    NOT_OWNER = "You are not owner of this item / plz insert a valid code"
    PRICE_FETCH_ERROR = "⚠️ Sorry, I couldn't fetch the latest prices right now.\n\nPlease try again in a few minutes."

    # Button labels
    CHAT_BUTTON = "ChaT"
    TOROB_BUTTON = "Torob price check"
    GOLD_DOLLAR_BUTTON = "Gold & Dollar"
    PROFILE_BUTTON = "profile"
    COMPLETE_PROFILE_BUTTON = f"Complete/Profile"
    RANDOM_CHAT_BUTTON = "Random chat"
    ADVANCE_SEARCH_BUTTON = "Advance Search"
    ADD_ITEM_BUTTON = "Add Item"
    CALCULATOR_BUTTON = "calculator"
    CHECK_ITEMS_BUTTON = "Check My Items/edit"
    ADD_NEW_ITEMS_BUTTON = "Add New items"

    # Filter labels
    DISTANCE_FILTER = "Distance"
    LAST_ONLINE_FILTER = "last Online"
    GENDER_FILTER = "Gender"
    AGE_FILTER = "Age"
    CITIES_FILTER = "Cities"
    SEARCH_BUTTON = "Search"
    DONE_BUTTON = "Done"
    ALL_BUTTON = "ALL"
    BACK_BUTTON = "Back"
    NEXT_BUTTON = "Next"

    # Profile display
    PROFILE_NOTE = "\nName:{gender_icon} {name}\nAge: {age} Years old\nLast Online: {last_online}\ncity: {city}\nDistance: {distance}km away\n\nuser_id: /chaT_{generated_id}\n\n{divider}\n"

    # Gold price display
    GOLD_PRICE_UPDATE = """✨💰 *GOLD PRICE UPDATE* 💰✨
    ___⏰ Updated @ {time}

    🇮🇷 *Iran Gold*
    🟡 18K 1g = {gold_18k_ir:,} Rial
    💵 Dollar = {dollar_ir_rial:,} Rial

    🌍 *International Gold*
    🟡 18K 1g = ${gold_18k_international_dollar}
    ➡️ Rial Equivalent = {gold_18k_international_rial:,} Rial

   """

    # Torob item display
    TOROB_ITEM_NOTE = "{signal}{name} @{latest_check}: with price of {latest_price}\n\nedit /item_{item_id}\n\n{divider}"
    TOROB_ITEM_UNCHECKED = "\n{signal}{name} is not yet Checked plz wait\n\nedit /item_{item_id}\n\n{divider}\n"

    # Status icons
    ONLINE_ICON = "Online"
    MALE_ICON = "👨🏻‍🦱"
    FEMALE_ICON = "👩🏻"
    PRICE_OK_ICON = "✅"
    PRICE_HIGH_ICON = "❌"
    DIVIDER = "〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"

    # General messages
    NOT_IN_CHAT = "⚠️ You're not in an active chat. Use /start to begin."
    CHAT_LEFT = "✅ You've left the chat. Use /start to generate a new link.\n\n⚠️ Delete ALL your sent messages?"
    PARTNER_LEFT = "❌ Your partner has left the chat."
    WHAT_ELSE = "what else i can do for you."
    SECRET_MODE_ACTIVATED = "activated 🔒"
    SECRET_MODE_DEACTIVATED = "deactivated 🔓"
    SECRET_MODE_NOTE = "\n\nℹ️ Media will be blurred and protected from saving."

    # Link messages
    ANON_CHAT_LINK = "🔗 Your private chat link:\n`{token}`\n\nShare it to let others chat with you anonymously!"
    ANON_MSG_LINK = "🔗 Your private Message link:\n`{token}`\n\nShare it to let others can send you anonymous message to you anonymously!"
    INVALID_LINK = "⚠️ This link is invalid or has expired.\n\nPlease ask your friend for a new link."
    SELF_CHAT_ERROR = "❌ You can't chat with yourself!"
    LINK_EXPIRED = "❌ The link is wrong or has been expire"

    # Connection messages
    STRANGER_JOINED = "🔄 A stranger has joined your chat! Say hello :)"
    CONNECTED_STRANGER = "🔄 Connected to a stranger! Start chatting."
    CONNECTED = "✅ Connected! Start chatting now"
    CONNECTION_FAILED = "❌ Failed to establish connection. Please try again."

    # Random chat messages
    SEARCHING_PARTNER = "🔍 Searching for a random chat partner..."
    PARTNER_TIMEOUT = "⏳ Could not find a partner in time. Try again later!"
    RANDOM_CHAT_ERROR = "Couldn't start random chat search"

    # Request messages
    BLOCKED_FROM_USER_WARNING = "You are Blocked by user"
    ACTIVE_CHAT_WARNING = "You are in active chat first leave chat"
    REQUEST_SENT = "you chat request for /chaT_{target_id} \n sent plz wait for answer"
    REQUEST_RECEIVED = "user: /chaT_{user_id} \nrequested to chat with you"
    BUSY_USER = (
        "user txting another user /chaT_{target_id} \n plz w8 until it is finished"
    )
    INVALID_USER = "invalid user id"

    # Edit/Delete messages
    MESSAGE_DELETED = "🗑️ Deleted {deleted_count} messages"
    DELETE_FAILED = " ({failed_count} failed)"
    DELETE_NOTIFICATION = "⚠️ Your partner has deleted their messages"
    DELETE_ERROR = "❌ Error deleting messages"
    EDIT_PREFIX = "✏️edited: "

    # Profile class messages
    PROFILE_START = "Lets create your profile.\n First send me your name"
    PROFILE_ASK_AGE = "What's your age?"
    PROFILE_INVALID_AGE = (
        "⚠️ Please enter a valid age between 13-120.\n\nHow old are you?"
    )
    PROFILE_AGE_NOT_NUMBER = "❌ That doesn't look like a valid age.\n\nPlease enter your age as a number (e.g. 25):"
    PROFILE_ASK_GENDER = "Select your gender:"
    PROFILE_ASK_ABOUT = "Tell me something about yourself (max 200 characters):"
    PROFILE_ABOUT_TOO_LONG = "Please keep it under 200 characters!"
    PROFILE_ASK_LOCATION = "Finally, share your location:"
    PROFILE_COMPLETE = "Profile creation cancelled"

    PROFILE_DISPLAY = """
    -
    🏷 Name: {name}
    🔢 Age: {age}
    👤 Gender: {gender}
    📝 About: {about}
    🕰 online: {last_online}

    user_id: /chaT_{generated_id}
    """

    # Direct message related
    DIRECT_MSG_PROMPT = "Plz send Your msg"
    DIRECT_MSG_TOO_LONG = "Message is too long. Please keep it under 250 characters."
    DIRECT_MSG_SENT = (
        "Your message request has been sent. The recipient will be notified."
    )
    DIRECT_MSG_REQUEST = (
        "User /chaT_{user_id} wants to send you a message. Do you want to accept it?"
    )
    DIRECT_MSG_ERROR = (
        "There was an issue sending your message request. Please try again."
    )
    DIRECT_MSG_ACCEPTED = "Accepted: msgs from /chaT_{target_id}"
    DIRECT_MSG_DECLINED = "Declined: msgs from /chaT_{target_id}"
    DIRECT_MSG_RECEIVED = "/chaT_{user_id}:Received your Messages"
    DIRECT_MSG_DECLINE_NOTIFY = "/chaT_{user_id} declined ur direct messages"
    DIRECT_MSG_NO_MSGS = "No messages to retrieve from /chaT_{target_id}"
    DIRECT_MSG_FAILED_DECLINE = (
        "Failed to decline or no messages to clear from /chaT_{target_id}"
    )

    # Calculator messages
    CALCULATOR_START = "Let's calculate it. \nFirst what item we will calculate"
    CALCULATOR_INVALID_ITEM = "This item is not in our list plz Enter another:"
    CALCULATOR_ASK_AMOUNT = "OK! How much of {item}:\n (gold: gram)"
    CALCULATOR_ASK_CONSTRUCTION_FEE = "Plz send contraction fee percentage: (1 to 100)"
    CALCULATOR_ASK_SHOP_FEE = "Plz send shop fee percentage: (1 to 100)"
    CALCULATOR_ASK_TEXT_FEE = "Plz send text percentage: (1 to 100)"
    CALCULATOR_RESULT = """item : {item} 
    amount: {amount}
    construction fee: {const_fee}%
    shop fee: {shop_fee}%
    text: {text_fee}%"""
    CALCULATOR_STOPPED = "Calculator stopped"

    # Torob messages
    TOROB_ADD_START = (
        "Lets add new item to your torob list \n What is name of Item (less that 150)"
    )
    TOROB_INVALID_NAME_LENGTH = "Please enter a string with less than 150 characters!"
    TOROB_ASK_PRICE = "Plz enter highest price that ur interest in {name}"
    TOROB_INVALID_PRICE = (
        "❌ Please enter a valid price (numbers only).\n\nExample: 1250000"
    )
    TOROB_PRICE_TOO_LOW = "❌ Price must be greater than 0.\n\nPlease enter the maximum price you're willing to pay:"
    TOROB_ASK_URL = (
        "plz gimme the url from torob that is for {name}\nhttps://torob.com/"
    )
    TOROB_INVALID_URL = "plz send a torob url "
    TOROB_ADD_SUCCESS = (
        "{name}: highest price {price}\nwith ur provided url added\n\n/start"
    )
    TOROB_ADD_FAILED = (
        "Failed to add item. Please ensure the URL is valid and try again."
    )
    TOROB_NOT_OWNER = "This item does not belong to you. Please enter a valid item ID."
    TOROB_DELETE_PROMPT = "Confirm delete with any word \n\nfor cancel type: /cancel"
    TOROB_ASK_NEW_PRICE = "Please enter new price"
    TOROB_ASK_NEW_URL = "Please enter new URL"
    TOROB_ASK_NEW_NAME = "Please enter new name"
    TOROB_UPDATE_SUCCESS = "✅ Item updated successfully!\n\nItem: {name}\nCurrent Highest Price: {price}\n\nCurrent URL: {url}\n\nWhat would you like to edit next?"
    TOROB_DELETE_SUCCESS = "✅ Item Deleted successfully!\n\n/start"
    TOROB_URL_UPDATE_FAILED = (
        "Failed to update URL. Please try again with a valid Torob URL."
    )
    TOROB_NAME_UPDATE_FAILED = "Failed to update name. Please try again."

    # Common messages
    OPERATION_CANCELLED = "Operation cancelled"
    TEXT_INPUT_REQUIRED = "Please send a text message"

    CREATE_ANON_CHAT = "createanonymousChat"
    CREATE_ANON_MSG = "createanonymousMsg"

    # ==============================================
    # Stable Patterns and Technical Constants (Bottom)
    # ==============================================

    # Button patterns
    test = "test"

    # Core patterns (should rarely change)
    REL_STARTER_PATTERN = "rel to rel"
    REL_INSPECT_PATTERN = "rel what what"
    LIKE_PATTERN = "it like it"
    FRIEND_PATTERN = "it add it"
    BLOCK_PATTERN = "it block it"
    REPORT_PATTERN = "it report it"
    UNLIKE_PATTERN = "it unlike it"
    UNFRIEND_PATTERN = "it unadd it"
    UNBLOCK_PATTERN = "it unblock it"
    PROFILE_EDIT_PATTERN = "I EDIT ME"
    NAME_PATTERN = "namae"
    ABOUT_PATTERN = "manan"
    CITY_PATTERN = "shahrmahr"
    PHOTO_PATTERN = "axmax"
    LOCATION_PATTER = "ja jo ja"
    LANGUAGE_PATTERN = "taghirzaban"
    QUERY_PATTERN_FILTERED_PPL = "gettingfilteredppl"

    # Gender options (stable)
    MALE_OPTION = "Male"
    FEMALE_OPTION = "Female"

    # Time options (stable)
    TIME_15MIN = "15min"
    TIME_30MIN = "30min"
    TIME_1HR = "1hr"
    TIME_3HR = "3hr"
    TIME_1DAY = "1day"
    TIME_1WEEK = "1week"

    # Distance options (stable)
    DISTANCE_5KM = "5km"
    DISTANCE_10KM = "10km"
    DISTANCE_15KM = "15km"
    DISTANCE_20KM = "20km"
    DISTANCE_25KM = "25km"
    DISTANCE_30KM = "30km"

    # Button labels (stable UI elements)
    LEAVE_BUTTON = "LeaveChat"
    SECRET_BUTTON = "SecretChat"
    DELETE_BUTTON = "ConfirmDeleteChat"
    RETRY_BUTTON = "↻ Retry"
    CANCEL_BUTTON = "✖ Cancel"
    SHARE_BUTTON = "Share this link!!"
    ACCEPT_BUTTON = "Accept"
    DENY_BUTTON = "Deny"

    # Command names (stable)

    BUTTON_PREFIX = "usermessagehandlerStarter"
    ACCEPT_CMD = "acceptchat"
    DENY_CMD = "denychat"

    # Regex patterns (should rarely change)
    TOROB_SCRAPER_TITLE = "Torob Scraper: "
    ITEM_CHECKED_FORMAT = "{signal}{name} @{latest_check}: with price of {latest_price}\n\nedit /item_{item_id}\n\n{divider}"
    ITEM_UNCHECKED_FORMAT = "\n{signal}{name} is not yet Checked plz wait\n\nedit /item_{item_id}\n\n{divider}\n"
    CHAT_REGEX = rf"^{CHAT_BUTTON}$"
    ADVANCE_SEARCH_REGEX = r"^Advance Search$"
    # RANDOM_CHAT_REGEX = r"^Random chat$"
    GOLD_DOLLAR_REGEX = r"^Gold & Dollar$"
    # TOROB_REGEX = r"^Torob price check$"
    ITEM_EDIT_REGEX = r"^/item_"
    CHAT_PROFILE_REGEX = r"^/chaT_"
