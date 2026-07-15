import logging
import re
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

NAME, PHOTO, CONFIRM = range(3)
registration_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    telegram_id = user.id

    existing_student = get_student_by_telegram(telegram_id)
    if existing_student:
        status = existing_student['status']
        if status == 'pending':
            await update.message.reply_text(
                "⏳ *طلبك قيد المراجعة*\n\nطلب تسجيلك قيد المراجعة حالياً من قبل الإدارة.\nسيتم إعلامك فور صدور القرار.",
                parse_mode=ParseMode.MARKDOWN
            )
        elif status == 'approved':
            await update.message.reply_text(
                f"✅ *أنت مسجل مسبقاً*\n\nأنت بالفعل طالب مسجل في SOMAR School.\nرقمك الطلابي: `{existing_student['student_number']}`",
                parse_mode=ParseMode.MARKDOWN
            )
        elif status == 'rejected':
            await update.message.reply_text(
                "❌ *تم رفض طلبك مسبقاً*\n\nنأسف لإعلامك أن طلب تسجيلك السابق تم رفضه.\nللتواصل مع الإدارة: @SOMAR_Admin",
                parse_mode=ParseMode.MARKDOWN
            )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎓 *مرحباً بك في SOMAR School*\n\nلبدء عملية التسجيل، نحتاج بعض المعلومات.\n\n📝 *الخطوة 1/3:* أدخل اسمك الكامل",
        parse_mode=ParseMode.MARKDOWN
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("⚠️ الاسم قصير جداً. الرجاء إدخال اسمك الكامل (3 أحرف على الأقل).")
        return NAME

    telegram_id = update.effective_user.id
    registration_data[telegram_id] = {'name': name}

    await update.message.reply_text(
        f"✅ تم حفظ الاسم: *{name}*\n\n📸 *الخطوة 2/3:* أرسل صورة شخصية واضحة",
        parse_mode=ParseMode.MARKDOWN
    )
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id

    if not update.message.photo:
        await update.message.reply_text("⚠️ الرجاء إرسال صورة مباشرة وليس كملف.")
        return PHOTO

    photo = update.message.photo[-1]
    file_id = photo.file_id
    registration_data[telegram_id]['photo_file_id'] = file_id
    name = registration_data[telegram_id]['name']

    await update.message.reply_photo(
        photo=file_id,
        caption=f"📋 *تأكيد معلومات التسجيل*\n\n👤 *الاسم:* {name}\n\n⚡ *الخطوة 3/3:* اكتب أي كلمة للتأكيد أو *إلغاء* للتراجع",
        parse_mode=ParseMode.MARKDOWN
    )
    return CONFIRM

async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    if "إلغاء" in text:
        if telegram_id in registration_data:
            del registration_data[telegram_id]
        await update.message.reply_text("🔄 *تم إلغاء التسجيل*\n\nيمكنك البدء من جديد باستخدام /start", parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    user_data = registration_data.get(telegram_id)
    if not user_data:
        await update.message.reply_text("⚠️ حدث خطأ. الرجاء البدء من جديد باستخدام /start")
        return ConversationHandler.END

    name = user_data['name']
    photo_file_id = user_data['photo_file_id']
    username = update.effective_user.username

    student_id = add_student(
        telegram_id=telegram_id,
        full_name=name,
        username=username,
        photo_file_id=photo_file_id
    )

    if student_id:
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo_file_id,
                    caption=f"🆕 *طلب تسجيل جديد*\n\n👤 *الاسم:* {name}\n🆔 *Telegram ID:* `{telegram_id}`\n📅 *الحالة:* ⏳ في انتظار المراجعة",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        del registration_data[telegram_id]

        await update.message.reply_text(
            f"🎉 *تم إرسال طلبك بنجاح!*\n\n👤 الاسم: {name}\n⏳ *طلبك قيد المراجعة*\n\nستصلك رسالة فور الموافقة أو الرفض.\n\n📞 *للاستفسار:* @SOMAR_Admin",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("❌ *حدث خطأ أثناء التسجيل*\n\nيرجى المحاولة مرة أخرى لاحقاً.", parse_mode=ParseMode.MARKDOWN)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    if telegram_id in registration_data:
        del registration_data[telegram_id]
    await update.message.reply_text("🛑 *تم إلغاء العملية*\n\nيمكنك البدء مرة أخرى باستخدام /start", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎓 *SOMAR School - مساعدة*\n\n🚀 /start - بدء التسجيل\nℹ️ /help - عرض هذه المساعدة\n❌ /cancel - إلغاء العملية",
        parse_mode=ParseMode.MARKDOWN
    )

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
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    logger.info("Student bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
