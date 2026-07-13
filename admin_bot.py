from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from config import ADMIN_BOT_TOKEN, ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "❌ ليس لديك صلاحية الدخول إلى لوحة الإدارة."
        )
        return

    keyboard = [
        ["👨‍🎓 طلبات التسجيل"],
        ["📋 الطلاب"],
        ["⚙️ الإعدادات"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🏫 SOMAR School Admin\n\n"
        "مرحباً مدير المدرسة 👋\n\n"
        "اختر العملية المطلوبة:",
        reply_markup=reply_markup
    )


def main():

    app = Application.builder().token(
        ADMIN_BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    print("Admin Bot Started...")

    app.run_polling()


if __name__ == "__main__":
    main()
