from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from config import BOT_TOKEN
from database import create_table


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

    photo_path = f"{update.effective_user.id}.jpg"

    await file.download_to_drive(photo_path)

    name = context.user_data["name"]

    await update.message.reply_text(
        f"✅ تم تسجيل بياناتك\n\n"
        f"👤 الاسم: {name}\n"
        "⏳ سيتم إنشاء الهوية المدرسية قريباً."
    )

    return ConversationHandler.END



def main():

    create_table()

    app = Application.builder().token(BOT_TOKEN).build()


    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],

        states={
            NAME: [
                MessageHandler(
                    filters.TEXT,
                    get_name
                )
            ],

            PHOTO: [
                MessageHandler(
                    filters.PHOTO,
                    get_photo
                )
            ]
        },

        fallbacks=[]
    )


    app.add_handler(conv)


    print("Student Bot Started...")


    app.run_polling()



if __name__ == "__main__":
    main()
