import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# CONVERSATION STATES
# ============================================
PHONE, PASSWORD = range(2)

# ============================================
# PAGINATION SETTINGS
# ============================================
ITEMS_PER_PAGE = 5

# ============================================
# CAR INVENTORY DATABASE
# ============================================
CAR_INVENTORY = [
    {
        "name": "Tesla Model 3",
        "price": "4,628,733,300 ﷼",
        "inventory": 15
    },
    {
        "name": "BMW X5",
        "price": "6,632,472,000 ﷼",
        "inventory": 8
    },
    {
        "name": "Mercedes-Benz C-Class",
        "price": "4,689,028,500 ﷼",
        "inventory": 12
    },
    {
        "name": "Toyota Camry",
        "price": "2,844,641,400 ﷼",
        "inventory": 25
    },
    {
        "name": "Honda Accord",
        "price": "3,002,916,300 ﷼",
        "inventory": 20
    },
    {
        "name": "Audi A4",
        "price": "4,403,703,000 ﷼",
        "inventory": 10
    },
    {
        "name": "Porsche 911",
        "price": "12,500,000,000 ﷼",
        "inventory": 3
    },
    {
        "name": "Ford Mustang",
        "price": "5,800,000,000 ﷼",
        "inventory": 7
    },
    {
        "name": "Chevrolet Corvette",
        "price": "7,200,000,000 ﷼",
        "inventory": 5
    },
    {
        "name": "Lexus RX",
        "price": "6,100,000,000 ﷼",
        "inventory": 14
    },
    {
        "name": "Range Rover Sport",
        "price": "9,500,000,000 ﷼",
        "inventory": 6
    }
]

# ============================================
# AUTHENTICATION SETTINGS
# ============================================
VALID_PASSWORD = "demo123"  # Simple demo password

# ============================================
# COMMAND HANDLERS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start command handler - initiates the conversation flow.
    Sends welcome message and requests phone number.
    """
    user = update.effective_user

    # Create a keyboard with "Share Contact" button
    keyboard = [[KeyboardButton("📱 اشتراک گزاری شماره تلفن", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    welcome_message = (
        f"👋 به ربات نمایشگاه خودرو خوش آمدید, {user.first_name}!\n\n"
        "برای شروع، لطفاً شماره تلفن خود را با استفاده از دکمهٔ زیر به اشتراک بگذارید، یا آن را به صورت دستی تایپ کنید (مثال: ۹۸۹۱۲۳۴۵۶۷۸۷+)."
    )

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles phone number input (either shared contact or manual text).
    Stores phone number and requests password.
    """
    # Check if user shared contact via button
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data['phone'] = phone_number

        await update.message.reply_text(
            f"✅ شماره تلفن شما تایید شد: {phone_number}",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        # User typed phone number manually
        phone_number = update.message.text.strip()
        context.user_data['phone'] = phone_number

        await update.message.reply_text(
            f"✅ شماره تلفن ذخیره شد: {phone_number}",
            reply_markup=ReplyKeyboardRemove()
        )

    # Request password
    await update.message.reply_text(
        "🔐 لطفا رمز خود را وارد کنید:\n\n",
        parse_mode='HTML'
    )

    return PASSWORD

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Validates password and displays car inventory if correct.
    """
    password = update.message.text.strip()
    phone = context.user_data.get('phone', 'Unknown')

    # Validate password
    if password == VALID_PASSWORD:
        await update.message.reply_text("✅ رمز عبور تایید شد")

        # Display first page of car inventory
        await send_car_page(update, context, page=0)

        # Log successful authentication
        logger.info(f"User {update.effective_user.id} authenticated successfully with phone {phone}")

        # End conversation
        await update.message.reply_text(
            "برای خرید به @sales پیام دهید"
        )

        return ConversationHandler.END
    else:
        # Invalid password
        await update.message.reply_text(
            "❌ رمز عبور اشتباه است. لطفا دوباره تلاش کنید.\n\n"
            f"<i>راهنما: رمز نمایشی {VALID_PASSWORD} است</i>",
            parse_mode='HTML'
        )

        return PASSWORD

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the conversation flow.
    """
    await update.message.reply_text(
        "🚫 عملیات لغو شد. برای شروع مجدد /start را تایپ کنید.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

# ============================================
# PAGINATION HANDLERS
# ============================================

async def send_car_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """
    Sends a paginated view of the car inventory.
    """
    total_cars = len(CAR_INVENTORY)
    total_pages = (total_cars + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE  # Ceiling division

    # Ensure page is within bounds
    if page < 0:
        page = 0
    elif page >= total_pages:
        page = total_pages - 1

    # Calculate start and end indices
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_cars)

    # Get cars for current page
    cars_on_page = CAR_INVENTORY[start_idx:end_idx]

    # Format the message
    message = format_car_inventory(cars_on_page, page + 1, total_pages, start_idx)

    # Create navigation buttons
    keyboard = []
    buttons_row = []

    # Previous button
    if page > 0:
        buttons_row.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"page_{page-1}"))

    # Page indicator
    buttons_row.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="current_page"))

    # Next button
    if page < total_pages - 1:
        buttons_row.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"page_{page+1}"))

    keyboard.append(buttons_row)
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send or edit message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles pagination button callbacks.
    """
    query = update.callback_query
    await query.answer()

    # Parse callback data
    if query.data.startswith("page_"):
        page = int(query.data.split("_")[1])
        await send_car_page(update, context, page)
    elif query.data == "current_page":
        # Do nothing, just acknowledge the click
        pass

# ============================================
# HELPER FUNCTIONS
# ============================================

def format_car_inventory(cars: list, page_num: int, total_pages: int, start_idx: int) -> str:
    """
    Formats a subset of the car inventory into a beautiful HTML message.

    Args:
        cars: List of car dictionaries to display
        page_num: Current page number (1-indexed)
        total_pages: Total number of pages
        start_idx: Starting index in the full inventory
    """
    message = "🚗 <b>لیست ماشین های موجود</b>\n"
    message += f"صفحه {page_num} از {total_pages}\n"
    message += "=" * 35 + "\n\n"

    for idx, car in enumerate(cars, start=start_idx + 1):
        message += f"<b>{idx}. {car['name']}</b>\n"
        message += f"   💰 قیمت: <code>{car['price']}</code>\n"
        message += f"   📦 موجودی: <code>{car['inventory']} دستگاه</code>\n\n"

    message += "=" * 35 + "\n"
    message += "از دکمه های زیر برای مشاهده صفحات دیگر استفاده کنید"

    return message

# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """
    Main function to start the bot.
    """
    # Replace with your actual bot token from @BotFather
    import os
    BOT_TOKEN = os.environ.get("BOT_TOKEN")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Define conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE: [
                MessageHandler(filters.CONTACT, receive_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
            ],
            PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add handlers
    application.add_handler(conv_handler)

    # Add pagination callback handler (for button clicks)
    application.add_handler(CallbackQueryHandler(pagination_callback))

    # Log startup
    logger.info("🤖 Bot started successfully! Waiting for messages...")
    print("\n" + "="*50)
    print("✅ Bot is running!")
    print("📱 Open Telegram and send /start to your bot")
    print("⚠️  Press Ctrl+C to stop the bot")
    print("="*50 + "\n")

    # Start polling (for Colab/local testing)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ============================================
# RUN THE BOT
# ============================================

if __name__ == '__main__':
    main()
