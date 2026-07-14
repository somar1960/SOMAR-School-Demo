import logging
from io import BytesIO
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from config import ADMIN_BOT_TOKEN, ADMIN_CHAT_IDS
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
        await update.message.reply_text("❌ ليس لديك صلاحية الدخول إلى لوحة الإدارة.")
        return

    await update.message.reply_text(
        "🏫 *SOMAR School Admin*\n\n"
        "مرحبًا مدير المدرسة 👋\n\n"
        "استخدم القائمة لمراجعة الطلبات:\n"
        "👨‍🎓 /registrations - عرض طلبات التسجيل المعلقة",
        parse_mode=ParseMode.MARKDOWN
    )

async def registrations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_CHAT_IDS:
        return

    students = get_pending_students()
    if not students:
        await update.message.reply_text("✅ لا توجد طلبات تسجيل جديدة.")
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
            f"🆔 *Telegram ID:* `{student['telegram_id']}`\n"
            f"📅 *تاريخ التسجيل:* {student['created_at']}"
        )

        try:
            # Send photo directly using file_id from database
            await update.message.reply_photo(
                photo=student['photo_file_id'],
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await update.message.reply_text(
                caption + "\n\n⚠️ تعذر عرض الصورة",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        student_id = int(data.replace("approve_", ""))
        student = get_student(student_id)
        if not student:
            await query.edit_message_text("⚠️ الطالب غير موجود.")
            return

        # Approve in DB
        approved = approve_student(student_id)
        student_number = approved['student_number']

        # Notify student
        try:
            await context.bot.send_message(
                chat_id=student['telegram_id'],
                text=(
                    "🎉 *تهانينا! تم قبول تسجيلك*\n\n"
                    f"👤 الاسم: *{student['full_name']}*\n"
                    f"🔢 رقم الطالب: `{student_number}`\n\n"
                    "📱 *البطاقة المدرسية جاري إعدادها...*"
                ),
                parse_mode=ParseMode.MARKDOWN
            )

            # Generate ID card
            # Load student photo from Telegram using file_id
            photo_file = await context.bot.get_file(student['photo_file_id'])
            photo_bytes = BytesIO()
            await photo_file.download_to_memory(photo_bytes)
            photo_bytes.seek(0)

            # Load logo (optional: you can keep it local or also from Telegram)
            logo_bytes = None
            try:
                with open("logo.png", "rb") as f:
                    logo_bytes = BytesIO(f.read())
            except Exception:
                pass

            # Create card in memory
            card_image = create_student_card(
                name=student['full_name'],
                student_number=student_number,
                photo_bytes=photo_bytes,
                logo_bytes=logo_bytes,
                school_name="SOMAR School"
            )

            # Send card
            await context.bot.send_photo(
                chat_id=student['telegram_id'],
                photo=card_image,
                caption=(
                    "🪪 *بطاقتك المدرسية*\n\n"
                    f"🏫 SOMAR School\n"
                    f"👤 {student['full_name']}\n"
                    f"🔢 `{student_number}`"
                ),
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to send approval to student: {e}")
            await query.edit_message_text(
                f"✅ تم قبول الطالب {student['full_name']}\n"
                f"🆔 رقم الطالب: {student_number}\n\n"
                "⚠️ لكن تعذر إرسال الإشعار للطالب."
            )
            return

        await query.edit_message_text(
            text=(
                f"✅ *تم قبول الطالب*\n\n"
                f"👤 {student['full_name']}\n"
                f"🆔 `{student_number}`\n"
                f"📱 تم إرسال البطاقة للطالب"
            ),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data.startswith("reject_"):
        student_id = int(data.replace("reject_", ""))
        student = get_student(student_id)
        if not student:
            await query.edit_message_text("⚠️ الطالب غير موجود.")
            return

        reject_student(student_id)

        # Notify student
        try:
            await context.bot.send_message(
                chat_id=student['telegram_id'],
                text=(
                    "❌ *نأسف لإعلامك*\n\n"
                    f"عزيزي/عزيزتي {student['full_name']}،\n\n"
                    "بعد مراجعة طلب تسجيلك، لم يتم قبوله.\n\n"
                    "للتواصل مع الإدارة: @SOMAR_Admin"
                ),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send rejection to student: {e}")

        await query.edit_message_text(
            text=f"❌ تم رفض طلب {student['full_name']}",
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    application = Application.builder().token(ADMIN_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("registrations", registrations))
    application.add_handler(MessageHandler(filters.Regex("^👨‍🎓 طلبات التسجيل$"), registrations))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Admin bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
