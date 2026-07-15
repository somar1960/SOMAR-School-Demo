import logging
from io import BytesIO
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ParseMode
from config import ADMIN_BOT_TOKEN, STUDENT_BOT_TOKEN, ADMIN_CHAT_IDS
from database import get_pending_students, get_student, approve_student, reject_student
from utils.id_card import create_student_card

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        await update.message.reply_text("❌ ليس لديك صلاحية.")
        return

    await update.message.reply_text(
        "🏫 *SOMAR School Admin*\n\n"
        "الأوامر:\n"
        "/registrations - طلبات التسجيل",
        parse_mode=ParseMode.MARKDOWN
    )

async def registrations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        return

    students = get_pending_students()
    if not students:
        await update.message.reply_text("✅ لا توجد طلبات جديدة.")
        return

    for student in students:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"approve_{student['id']}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{student['id']}"),
            ]
        ])

        caption = (
            "📄 *طلب تسجيل جديد*\n\n"
            f"👤 *الاسم:* {student['full_name']}\n"
            f"🆔 *Telegram ID:* `{student['telegram_id']}`"
        )

        try:
            await update.message.reply_photo(
                photo=student['photo_file_id'],
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text(caption, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # استخدام بوت الطالب للمراسلة
    student_bot = Bot(token=STUDENT_BOT_TOKEN)

    if data.startswith("approve_"):
        student_id = int(data.replace("approve_", ""))
        student = get_student(student_id)
        if not student:
            await query.edit_message_text("⚠️ الطالب غير موجود.")
            return

        approved = approve_student(student_id)
        student_number = approved['student_number']

        try:
            # إشعار القبول
            await student_bot.send_message(
                chat_id=student['telegram_id'],
                text=f"🎉 *تم قبولك!*\n\n👤 {student['full_name']}\n🔢 رقمك: `{student_number}`",
                parse_mode=ParseMode.MARKDOWN
            )

            # تحضير البطاقة
            photo_file = await student_bot.get_file(student['photo_file_id'])
            photo_bytes = BytesIO()
            await photo_file.download_to_memory(photo_bytes)
            photo_bytes.seek(0)

            logo_bytes = None
            try:
                with open("logo.png", "rb") as f:
                    logo_bytes = BytesIO(f.read())
            except:
                pass

            card_image = create_student_card(
                name=student['full_name'],
                student_number=student_number,
                photo_bytes=photo_bytes,
                logo_bytes=logo_bytes,
                school_name="SOMAR School"
            )

            # إرسال البطاقة
            await student_bot.send_photo(
                chat_id=student['telegram_id'],
                photo=card_image,
                caption=f"🪪 *بطاقتك المدرسية*\n\n👤 {student['full_name']}\n🔢 `{student_number}`",
                parse_mode=ParseMode.MARKDOWN
            )

            await query.edit_message_text(f"✅ تم قبول {student['full_name']}\n🆔 {student_number}")

        except Exception as e:
            logger.error(f"Error: {e}")
            await query.edit_message_text(f"✅ تم القبول ولكن تعذر إرسال الإشعار للطالب.")

    elif data.startswith("reject_"):
        student_id = int(data.replace("reject_", ""))
        student = get_student(student_id)
        if not student:
            await query.edit_message_text("⚠️ الطالب غير موجود.")
            return

        reject_student(student_id)

        try:
            await student_bot.send_message(
                chat_id=student['telegram_id'],
                text=f"❌ *نأسف*\n\nعزيزي {student['full_name']}،\nطلبك لم يتم قبوله.\nراجع المدرسة للاستفسار.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error: {e}")

        await query.edit_message_text(f"❌ تم رفض {student['full_name']}")

def main():
    application = Application.builder().token(ADMIN_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("registrations", registrations))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Admin bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
