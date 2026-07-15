async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    text = update.message.text.strip()
    
    # تنظيف النص من الإيموجيات والمسافات الزائدة
    import re
    clean_text = re.sub(r'[^\u0621-\u064A\s]', '', text).strip()
    
    if clean_text == "تأكيد" or clean_text == "تاكيد":
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

    elif "إلغاء" in clean_text:
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
