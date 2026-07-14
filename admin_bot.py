from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import asyncio
import uuid

from config import ADMIN_BOT_TOKEN, ADMIN_IDS
from database import (
    get_pending_students,
    approve_student,
    reject_student,
    get_student
)

from utils.id_card import create_student_card

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

    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


    await update.message.reply_text(
        "🏫 SOMAR School Admin\n\n"
        "مرحباً مدير المدرسة 👋\n\n"
        "اختر العملية المطلوبة:",
        reply_markup=markup
    )



async def registrations(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        return

    students = get_pending_students()

    if not students:
        await update.message.reply_text(
            "✅ لا توجد طلبات تسجيل جديدة."
        )
        return

    for student in students:

        student_id = student[0]
        telegram_id = student[1]
        name = student[2]
        photo = student[3]

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "✅ قبول",
                    callback_data=f"approve_{student_id}"
                ),
                InlineKeyboardButton(
                    "❌ رفض",
                    callback_data=f"reject_{student_id}"
                )
            ]]
        )

        text = (
            "📄 طلب تسجيل جديد\n\n"
            f"👤 الاسم: {name}\n"
            f"🆔 Telegram ID: {telegram_id}"
        )

        try:
            with open(photo, "rb") as image:
                await update.message.reply_photo(
                    photo=image,
                    caption=text,
                    reply_markup=keyboard
                )
        except Exception:
            await update.message.reply_text(
                text,
                reply_markup=keyboard
            )

        except Exception:

            await update.message.reply_text(
                text,
                reply_markup=keyboard
            )



async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    data = query.data


if data.startswith("approve_"):

    student_id = int(
        data.replace(
            "approve_",
            ""
        )
    )

    student_number = (
        "SOMAR-"
        +
        str(uuid.uuid4())[:8].upper()
    )

    student = get_student(student_id)

    approve_student(
        student_id,
        student_number
    )

    card_path = create_student_card(
        name=student[2],
        student_number=student_number,
        photo_path=student[3],
        logo_path="logo.png"
    )

    await query.edit_message_text(
        text=
        "✅ تم قبول الطالب\n\n"
        f"🆔 رقم الطالب: {student_number}"
    )

    try:

        await context.bot.send_photo(
            chat_id=student[1],
            photo=open(card_path, "rb"),
            caption=
            "🎉 تم قبول طلب التسجيل.\n\n"
            f"🆔 رقمك المدرسي:\n{student_number}"
        )

    except Exception as e:
        print(e)
        
        elif data.startswith("reject_"):
    
        student_id = int(
            data.replace(
                "reject_",
                ""
            )
        )


        reject_student(
            student_id
        )


        student = get_student(student_id)


        await query.edit_message_text(
    text="❌ تم رفض طلب التسجيل."
)


        try:

            await context.bot.send_message(
                chat_id=student[1],
                text=
                "❌ نعتذر، تم رفض طلب التسجيل في SOMAR School."
            )

        except:
            pass




async def run_bot():

    app = Application.builder().token(
        ADMIN_BOT_TOKEN
    ).build()


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(
                "^👨‍🎓 طلبات التسجيل$"
            ),
            registrations
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    await app.initialize()
    await app.start()
    await app.updater.start_polling()


    print(
        "Admin Bot Started..."
    )


    await asyncio.Event().wait()



if __name__ == "__main__":
    asyncio.run(run_bot())
