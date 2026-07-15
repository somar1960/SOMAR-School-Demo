import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from config import STUDENT_BOT_TOKEN, ADMIN_CHAT_IDS
from database import create_table, get_student_by_telegram, add_student

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
NAME, PHOTO, CONFIRM = range(3)

# Temporary storage for registration data
registration_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    telegram_id = user.id

    # Check if student already exists
    existing_student = get_student_by_telegram(telegram_id)
    if existing_student:
        status = existing_student['status']
        if status == 'pending':
            await update.message.reply_text(
                "⏳ *طلبك قيد المراجعة*\n\n"
                "طلب تسجيلك قيد المراجعة حاليًا من قبل الإدارة.\n"
                "سيتم إعلامك فور صدور القرار.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif status == 'approved':
            await update.message.reply_text(
                "✅ *أنت مسجل مسبقًا*\n\n"
                "أنت بالفعل طالب مسجل في SOMAR School.\n"
                f"رقمك الطلابي: `{existing_student['student_number']}`\n\n"
                "إذا فقدت بطاقتك المدرسية، تواصل مع الإدارة.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif status == 'rejected':
            await update.message.reply_text(
                "❌ *تم رفض طلبك مسبقًا*\n\n"
                "نأسف لإعلامك أن طلب تسجيلك السابق تم رفضه.\n"
                "للتواصل مع الإدارة: @SOMAR_Admin",
                parse_mode=ParseMode.MARKDOWN
            )
        return ConversationHandler.END

    # New student
    await update.message.reply_text(
        "🎓 *مرحبًا بك في SOMAR School*\n\n"
        "لبدء عملية التسجيل، نحتاج بعض المعلومات.\n\n"
        "📝 *الخطوة 1/3:* أدخل اسمك الكامل\n\n"
        "مثال: أحمد محمد علي",
        parse_mode=ParseMode.MARKDOWN
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("⚠️ الاسم قصير جدًا. الرجاء إدخال اسمك الكامل (3 أحرف على الأقل).")
        return NAME
    if len(name) > 100:
        await update.message.reply_text("⚠️ الاسم طويل جدًا. الرجاء إدخال اسم لا يتجاوز 100 حرف.")
        return NAME

    telegram_id = update.effective_user.id
    registration_data[telegram_id] = {'name': name}

    await update.message.reply_text(
        f"✅ تم حفظ الاسم: *{name}*\n\n"
        "📸 *الخطوة 2/3:* أرسل صورة شخصية واضحة\n\n"
        "*ملاحظات مهمة:*\n"
        "• يجب أن تكون الصورة واضحة ومباشرة\n"
        "• يفضل أن تكون بخلفية بيضاء\n"
        "• لا تقبل الصور الجماعية\n"
        "• أرسل الصورة كصورة مباشرة (وليس كملف)",
        parse_mode=ParseMode.MARKDOWN
    )
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id

    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ *الرجاء إرسال صورة*\n\n"
            "يجب إرسال الصورة كصورة مباشرة، وليس كملف أو مستند.\n"
            "حاول مرة أخرى بإرسال صورة واضحة.",
            parse_mode=ParseMode.MARKDOWN
        )
        return PHOTO

    # Get the largest photo
    photo = update.message.photo[-1]
    file_id = photo.file_id

    registration_data[telegram_id]['photo_file_id'] = file_id
    name = registration_data[telegram_id]['name']

    await update.message.reply_photo(
        photo=file_id,
        caption=(
            "📋 *تأكيد معلومات التسجيل*\n\n"
            f"👤 *الاسم:* {name}\n"
            f"🆔 *معرف التليجرام:* `{telegram_id}`\n\n"
            "⚡ *الخطوة 3/3:* هل تؤكد صحة المعلومات؟\n\n"
            "أرسل:\n"
            "✅ *تأكيد* - لإرسال الطلب\n"
            "❌ *إلغاء* - للبدء من جديد"
        ),
        parse_mode=ParseMode.MARKDOWN
    )
    return CONFIRM

async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    if "تأكيد" in text or "تاكيد" in text:
        user_data = registration_data.get(telegram_id)
        if not user_data:
            await update.message.reply_text("⚠️ حدث خطأ. الرجاء البدء من جديد باستخدام /start")
            return ConversationHandler.END

        name = user_data['name']
        photo_file_id = user_data['photo_file_id']
        username = update.effective_user.username

        # Save to database
        student_id = add_student(
            telegram_id=telegram_id,
            full_name=name,
            username=username,
            photo_file_id=photo_file_id
        )

        if student_id:
            # Notify admins
            for admin_id in ADMIN_CHAT_IDS:
                try:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=photo_file_id,
                        caption=(
                            "🆕 *طلب تسجيل جديد*\n\n"
                            f"👤 *الاسم:* {name}\n"
                            f"🆔 *Telegram ID:* `{telegram_id}`\n"
                            "📅 *الحالة:* ⏳ في انتظار المراجعة\n\n"
                            "استخدم بوت الإدارة للمراجعة."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")

            # Clear temp data
            del registration_data[telegram_id]

            await update.message.reply_text(
                "🎉 *تم إرسال طلبك بنجاح!*\n\n"
                f"👤 الاسم: {name}\n"
                "⏳ *طلبك قيد المراجعة*\n\n"
                "سيقوم فريق الإدارة بمراجعة طلبك.\n"
                "ستصلك رسالة فور الموافقة أو الرفض.\n\n"
                "📞 *للاستفسار:* @SOMAR_Admin",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "❌ *حدث خطأ أثناء التسجيل*\n\n"
                "يرجى المحاولة مرة أخرى لاحقًا أو التواصل مع الإدارة.",
                parse_mode=ParseMode.MARKDOWN
            )
        return ConversationHandler.END

    elif text == "❌ إلغاء" or text.lower() == "إلغاء":
        if telegram_id in registration_data:
            del registration_data[telegram_id]
        await update.message.reply_text(
            "🔄 *تم إلغاء التسجيل*\n\n"
            "يمكنك البدء من جديد في أي وقت باستخدام /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "⚠️ *خيار غير صحيح*\n\n"
            "الرجاء الرد بـ:\n"
            "✅ *تأكيد* - لإرسال الطلب\n"
            "❌ *إلغاء* - للبدء من جديد",
            parse_mode=ParseMode.MARKDOWN
        )
        return CONFIRM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    if telegram_id in registration_data:
        del registration_data[telegram_id]
    await update.message.reply_text(
        "🛑 *تم إلغاء العملية*\n\n"
        "يمكنك البدء مرة أخرى باستخدام /start",
        parse_mode=ParseMode.MARKDOWN
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🎓 *SOMAR School - مساعدة*\n\n"
        "*الأوامر المتاحة:*\n"
        "🚀 /start - بدء التسجيل أو عرض الحالة\n"
        "ℹ️ /help - عرض هذه المساعدة\n"
        "❌ /cancel - إلغاء العملية الحالية\n\n"
        "*للاستفسار:*\n"
        "📞 تواصل مع الإدارة: @SOMAR_Admin"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def main():
    create_table()
    application = Application.builder().token(STUDENT_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo),
            ],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_registration)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_user=True,
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    logger.info("Student bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
