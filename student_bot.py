from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

import asyncio

from config import BOT_TOKEN
from database import create_table, add_student


NAME, PHOTO = range(2)


async def start(update: Update, context):
    await update.message.reply_text(
        "🎓 أهلاً بك في SOMAR School\n\n"
        "لإنشاء هويتك المدرسية:\n"
        "أرسل اسمك الثلاثي."
    )

    return NAME


async def get_name(update: Update, context):
    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "📸 الآن أرسل صورتك الشخصية."
    )

    return PHOTO


async def get_photo(update: Update, context):
    photo = update.message.photo[-1]

    file = await photo.get_file()

    photo_path = f"photos/{update.effective_user.id}.jpg"

    await file.download_to_drive(photo_path)

    name = context.user_data["name"]
    add_student(
    update.effective_user.id,
    name,
    photo_path
)
    await update.message.reply_text(
        "✅ تم تسجيل بياناتك\n\n"
        f"👤 الاسم: {name}\n"
        "⏳ جاري تجهيز الهوية المدرسية..."
    )

    return ConversationHandler.END


async def run_bot():

    create_table()

    app = Application.builder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],

        states={
            NAME: [
                MessageHandler(filters.TEXT, get_name)
            ],

            PHOTO: [
                MessageHandler(filters.PHOTO, get_photo)
            ]
        },

        fallbacks=[]
    )

    app.add_handler(conversation)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    print("Student Bot Started...")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(run_bot())
