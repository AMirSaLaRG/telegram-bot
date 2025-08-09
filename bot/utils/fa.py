from bot.utils.en import messages


class Messages(messages):
    # ==============================================
    # Frequently Changing Messages (Top) - Persian Translations
    # ==============================================

    # General messages
    START_MESSAGE = "شروع"
    WHAT_YOU_LOOKING_FOR = "به چه چیزی نیاز دارید؟"
    ADVANCE_SEARCH_TITLE = "جستجوی پیشرفته:"
    RANDOM_CHAT_PROMPT = "چت تصادفی می‌خواهید؟"
    CHOOSE_PROMPT = "انتخاب کنید"
    CHOOSE_GENDER = "جنسیت خود را انتخاب کنید:"
    CHOOSE_STARTING_AGE = "لطفا حداقل سن را انتخاب کنید:"
    NO_PROFILES_FOUND = "هیچ پروفایلی با این فیلتر یافت نشد\n\n/start"
    NOTHING_TO_SHOW = "چیزی برای نمایش وجود ندارد\n\n /start"
    ITEM_ON_EDIT_MODE = "✅ حالت ویرایش فعال!\n\nآیتم: {name}\nقیمت فعلی: {price}\n\nلینک فعلی: {url}\n\nچه تغییری می‌خواهید اعمال کنید؟"

    # Error messages
    INVALID_FORMAT = "قالب نامعتبر. از /{command}_<مقدار> استفاده کنید"
    INVALID_ITEM = "آیتم نامعتبر. این آیتم یافت نشد"
    USER_NOT_REGISTERED = "این کاربر ثبت‌نام نکرده است!"
    NOT_OWNER = "شما مالک این آیتم نیستید / لطفا کد معتبر وارد کنید"
    PRICE_FETCH_ERROR = "⚠️ خطا در دریافت قیمت‌ها\n\nلطفا چند دقیقه دیگر تلاش کنید."

    # Button labels
    CHAT_BUTTON = "چت"
    TOROB_BUTTON = "بررسی قیمت ترب"
    GOLD_DOLLAR_BUTTON = "قیمت طلا و دلار"
    PROFILE_BUTTON = "/پروفایل"
    CREATE_PROFILE_BUTTON = "/ایجاد_پروفایل"
    # RANDOM_CHAT_BUTTON = "چت تصادفی"
    ADVANCE_SEARCH_BUTTON = "جستجوی پیشرفته"
    ADD_ITEM_BUTTON = "افزودن آیتم"
    CALCULATOR_BUTTON = "ماشین حساب"
    CHECK_ITEMS_BUTTON = "مشاهده/ویرایش آیتم‌ها"
    ADD_NEW_ITEMS_BUTTON = "افزودن آیتم جدید"

    # Filter labels
    DISTANCE_FILTER = "فاصله"
    LAST_ONLINE_FILTER = "آخرین بازدید"
    GENDER_FILTER = "جنسیت"
    AGE_FILTER = "سن"
    CITIES_FILTER = "شهرها"
    SEARCH_BUTTON = "جستجو"
    DONE_BUTTON = "تایید"
    ALL_BUTTON = "همه"
    BACK_BUTTON = "بازگشت"
    NEXT_BUTTON = "بعدی"

    # Profile display
    PROFILE_NOTE = "\nنام:{gender_icon} {name}\nسن: {age} سال\nآخرین بازدید: {last_online}\nشهر: {city}\nفاصله: {distance} کیلومتر\n\nشناسه کاربری: /chaT_{generated_id}\n\n{divider}\n"

    # Gold price display
    GOLD_PRICE_UPDATE = ("""✨💰 *به‌روزرسانی قیمت طلا* 💰✨
        ___⏰ آخرین بروزرسانی: {time}

        🇮🇷 *قیمت داخلی*
        🟡 18 عیار: {gold_18k_ir:,} تومان
        💵 دلار: {dollar_ir_rial:,} تومان

        🌍 *قیمت جهانی*
        🟡 18 عیار: ${gold_18k_international_dollar}
        ➡️ معادل تومان: {gold_18k_international_rial:,} تومان

       """)

    # Torob item display
    TOROB_ITEM_NOTE = "{signal}{name} @{latest_check}: قیمت {latest_price}\n\nویرایش /item_{item_id}\n\n{divider}"
    TOROB_ITEM_UNCHECKED = "\n{signal}{name} هنوز بررسی نشده\n\nویرایش /item_{item_id}\n\n{divider}\n"

    # Status icons (kept same as they're visual)
    ONLINE_ICON = "آنلاین"
    MALE_ICON = "👨🏻‍🦱"
    FEMALE_ICON = "👩🏻"
    PRICE_OK_ICON = "✅"
    PRICE_HIGH_ICON = "❌"
    DIVIDER = '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️'

    # General messages
    NOT_IN_CHAT = "⚠️ شما در چت فعالی نیستید. /start را بزنید."
    CHAT_LEFT = "✅ چت را ترک کردید. /start را بزنید.\n\n⚠️ همه پیام‌هایتان حذف شود؟"
    PARTNER_LEFT = "❌ کاربر مقابل چت را ترک کرد."
    WHAT_ELSE = "چه کمکی دیگری می‌توانم بکنم؟"
    SECRET_MODE_ACTIVATED = "فعال شد 🔒"
    SECRET_MODE_DEACTIVATED = "غیرفعال شد 🔓"
    SECRET_MODE_NOTE = "\n\nℹ️ رسانه‌ها محافظت می‌شوند."

    # Link messages
    ANON_CHAT_LINK = "🔗 لینک چت خصوصی:\n`{token}`\n\nبرای چت ناشناس این لینک را به اشتراک بگذارید!"
    ANON_MSG_LINK = "🔗 لینک پیام خصوصی:\n`{token}`\n\nبرای دریافت پیام ناشناس این لینک را به اشتراک بگذارید!"
    INVALID_LINK = "⚠️ لینک نامعتبر یا منقضی شده\n\nلطفا لینک جدید دریافت کنید."
    SELF_CHAT_ERROR = "❌ نمی‌توانید با خودتان چت کنید!"
    LINK_EXPIRED = "❌ لینک نامعتبر یا منقضی شده"

    # Connection messages
    STRANGER_JOINED = "🔄 کاربر جدید به چت پیوست! سلام کنید :)"
    CONNECTED_STRANGER = "🔄 به یک کاربر متصل شدید! گفتگو را شروع کنید."
    CONNECTED = "✅ متصل شدید! گفتگو را شروع کنید."
    CONNECTION_FAILED = "❌ خطا در اتصال. لطفا مجددا تلاش کنید."

    # Random chat messages
    SEARCHING_PARTNER = "🔍 در حال یافتن کاربر..."
    PARTNER_TIMEOUT = "⏳ کاربری یافت نشد. مجددا تلاش کنید!"
    RANDOM_CHAT_ERROR = "خطا در شروع چت تصادفی"

    # Request messages
    BLOCKED_FROM_USER_WARNING = "شما توسط این کاربر مسدود شده‌اید"
    ACTIVE_CHAT_WARNING = "شما در چت فعال هستید. اول از چت خارج شوید"
    REQUEST_SENT = "درخواست چت برای /chaT_{target_id} ارسال شد"
    REQUEST_RECEIVED = "کاربر /chaT_{user_id} درخواست چت داده است"
    BUSY_USER = "کاربر /chaT_{target_id} مشغول است"
    INVALID_USER = "شناسه کاربر نامعتبر"

    # Edit/Delete messages
    MESSAGE_DELETED = "🗑️ {deleted_count} پیام حذف شد"
    DELETE_FAILED = " ({failed_count} خطا)"
    DELETE_NOTIFICATION = "⚠️ کاربر مقابل پیام‌هایش را حذف کرد"
    DELETE_ERROR = "❌ خطا در حذف پیام‌ها"
    EDIT_PREFIX = "✏️ویرایش: "

    # Profile class messages
    PROFILE_START = "برای ساخت پروفایل، ابتدا نام خود را وارد کنید"
    PROFILE_ASK_AGE = "سن شما چقدر است؟"
    PROFILE_INVALID_AGE = "⚠️ سن باید بین 13-120 باشد\n\nسن خود را وارد کنید:"
    PROFILE_AGE_NOT_NUMBER = "❌ سن نامعتبر\n\nلطفا عدد وارد کنید (مثال: 25):"
    PROFILE_ASK_GENDER = "جنسیت خود را انتخاب کنید:"
    PROFILE_ASK_ABOUT = "درباره خودتان بنویسید (حداکثر 200 کاراکتر):"
    PROFILE_ABOUT_TOO_LONG = "حداکثر 200 کاراکتر مجاز است!"
    PROFILE_ASK_LOCATION = "موقعیت مکانی خود را به اشتراک بگذارید:"
    PROFILE_COMPLETE = "ساخت پروفایل لغو شد"

    PROFILE_DISPLAY = """
        🏷 نام: {name}
        🔢 سن: {age}
        👤 جنسیت: {gender}
        📝 درباره: {about}
        🕰 آخرین بازدید: {last_online}

        شناسه کاربری: /chaT_{generated_id}
        """

    # Direct message related
    DIRECT_MSG_PROMPT = "پیام خود را بنویسید"
    DIRECT_MSG_TOO_LONG = "حداکثر 250 کاراکتر مجاز است"
    DIRECT_MSG_SENT = "درخواست پیام ارسال شد"
    DIRECT_MSG_REQUEST = "کاربر /chaT_{user_id} می‌خواهد با شما چت کند. قبول کنید؟"
    DIRECT_MSG_ERROR = "خطا در ارسال پیام. مجددا تلاش کنید."
    DIRECT_MSG_ACCEPTED = "پیام‌های /chaT_{target_id} پذیرفته شد"
    DIRECT_MSG_DECLINED = "پیام‌های /chaT_{target_id} رد شد"
    DIRECT_MSG_RECEIVED = "/chaT_{user_id}: پیام شما دریافت شد"
    DIRECT_MSG_DECLINE_NOTIFY = '/chaT_{user_id} پیام شما را رد کرد'
    DIRECT_MSG_NO_MSGS = 'پیامی از /chaT_{target_id} وجود ندارد'
    DIRECT_MSG_FAILED_DECLINE = 'خطا در رد پیام‌ها'

    # Calculator messages
    CALCULATOR_START = "محاسبه را شروع می‌کنیم\nابتدا نام آیتم را وارد کنید"
    CALCULATOR_INVALID_ITEM = "این آیتم در لیست ما نیست. آیتم دیگری وارد کنید:"
    CALCULATOR_ASK_AMOUNT = "مقدار {item} را وارد کنید:\n (طلا: گرم)"
    CALCULATOR_ASK_CONSTRUCTION_FEE = "درصد اجرت را وارد کنید (1 تا 100):"
    CALCULATOR_ASK_SHOP_FEE = "درصد فروشگاه را وارد کنید (1 تا 100):"
    CALCULATOR_ASK_TEXT_FEE = "درصد طلا را وارد کنید (1 تا 100):"
    CALCULATOR_RESULT = """آیتم: {item} 
        مقدار: {amount}
        اجرت: {const_fee}%
        فروشگاه: {shop_fee}%
        طلا: {text_fee}%"""
    CALCULATOR_STOPPED = "محاسبه متوقف شد"

    # Torob messages
    TOROB_ADD_START = "برای افزودن آیتم جدید، نام آن را وارد کنید (حداکثر 150 کاراکتر)"
    TOROB_INVALID_NAME_LENGTH = "حداکثر 150 کاراکتر مجاز است!"
    TOROB_ASK_PRICE = "حداکثر قیمت مورد نظر برای {name} را وارد کنید"
    TOROB_INVALID_PRICE = "❌ قیمت نامعتبر\n\nمثال: 1250000"
    TOROB_PRICE_TOO_LOW = "❌ قیمت باید بیشتر از 0 باشد"
    TOROB_ASK_URL = "لینک ترب مربوط به {name} را ارسال کنید"
    TOROB_INVALID_URL = "لینک ترب نامعتبر است"
    TOROB_ADD_SUCCESS = "{name} با قیمت {price} افزوده شد\n\n/start"
    TOROB_ADD_FAILED = "خطا در افزودن آیتم. لینک را بررسی کنید."
    TOROB_NOT_OWNER = "این آیتم متعلق به شما نیست"
    TOROB_DELETE_PROMPT = "برای حذف تأیید کنید\n\nلغو: /cancel"
    TOROB_ASK_NEW_PRICE = "قیمت جدید را وارد کنید"
    TOROB_ASK_NEW_URL = "لینک جدید را وارد کنید"
    TOROB_ASK_NEW_NAME = "نام جدید را وارد کنید"
    TOROB_UPDATE_SUCCESS = "✅ آیتم با موفقیت به‌روزرسانی شد!\n\nآیتم: {name}\nقیمت: {price}\n\nلینک: {url}\n\nچه تغییری می‌خواهید؟"
    TOROB_DELETE_SUCCESS = "✅ آیتم با موفقیت حذف شد!\n\n/start"
    TOROB_URL_UPDATE_FAILED = "خطا در به‌روزرسانی لینک"
    TOROB_NAME_UPDATE_FAILED = "خطا در به‌روزرسانی نام"

    # Common messages
    OPERATION_CANCELLED = "عملیات لغو شد"
    TEXT_INPUT_REQUIRED = "لطفا متن وارد کنید"

