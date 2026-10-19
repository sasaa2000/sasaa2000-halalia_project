"""
حلالية - منصة الذكاء الاصطناعي الحلال للمتسوقات
Message Handlers - النسخة النهائية مع جميع الأزرار
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram_bot.api_client import analyze_product

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية (أسماء المنتجات) مع صور"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not text or text.startswith('/'):
        return

    status_msg = await update.message.reply_text(f"⏳ جاري البحث والتحليل في حلالية: {text}...")

    try:
        result = analyze_product(text)

        if not result or "error" in result:
            await status_msg.edit_text(
                f"❌ عذراً، لم أتمكن من العثور على معلومات كافية عن '{text}'.\n"
                f"يرجى تجربة اسم آخر أو أكثر تحديداً."
            )
            return

        name = result.get("product_name", text)
        score = result.get("score", 0)
        price = result.get("sell_price", 0)
        rating = result.get("rating", 0)
        reviews = result.get("reviews", 0)
        rec = result.get("recommendation", "موصى به")
        image_url = result.get("image_url", "")

        demand = result.get("demand", "متوسط")
        competition = result.get("competition", "متوسطة")
        shipping = result.get("shipping", "سهل")
        google_trend = result.get("google_trend", 0)
        trend_direction = result.get("trend_direction", "محايد")

        # تقييم شامل
        if score >= 7:
            trust = "🌟 موثوق وعالي الجودة"
            halal_status = "✅ منتج موصى به"
        elif score >= 5:
            trust = "✅ جيد ومناسب"
            halal_status = "✅ مقبول مع مراعاة الحاجة"
        else:
            trust = "⚠️ يحتاج لمراجعة إضافية"
            halal_status = "️ يُنصح بالبحث عن بديل"

        # فحص القيمة مقابل السعر
        if score >= 7 and price > 0:
            value_check = "💎 قيمة ممتازة مقابل السعر."
        elif score < 5 and price > 50:
            value_check = "⚠️ السعر قد يكون مرتفعاً مقارنة بتقييمات المنتج."
        else:
            value_check = "💡 السعر معقول، لكن راجعي التقييمات جيداً."

        # نصائح ذكية
        tips = []
        if google_trend >= 60:
            tips.append("📈 المنتج مطلوب حالياً.")
        if shipping == "صعب":
            tips.append("🚚 الشحن قد يكون صعباً - تحققي من سياسة الإرجاع.")
        if reviews < 100:
            tips.append("⭐ التقييمات قليلة - يُنصح بقراءة المراجعات بعناية.")

        tips_text = "\n".join(tips) if tips else "💡 لا توجد ملاحظات خاصة."

        # بناء الرسالة
        message = (
            f"🛍️ <b>{name}</b>\n\n"
            f" السعر التقريبي: ${price}\n"
            f"⭐ التقييم: {rating}/5 (من {reviews} تقييم)\n"
            f"🤖 درجة الثقة: {score}/10\n\n"
            f"📊 <b>تحليل السوق:</b>\n"
            f"• الطلب: {demand} | المنافسة: {competition}\n"
            f"• الاتجاه: {trend_direction} ({google_trend}/100)\n\n"
            f"💡 <b>حكم حلالية:</b> {trust}\n"
            f"🎯 <b>التوصية:</b> {rec}\n"
            f"️ <b>الحالة:</b> {halal_status}\n"
            f"💎 <b>القيمة:</b> {value_check}\n\n"
            f"🔍 <b>نصائح ذكية:</b>\n{tips_text}"
        )

        # إضافة تقرير الحلال
        if 'halal_report' in result:
            message += "\n\n" + result['halal_report']
        elif result.get('halal_status') == 'haram':
            message += "\n\n <b>تنبيه مهم:</b> هذا المنتج غير حلال"
        elif result.get('halal_status') == 'doubtful':
            message += "\n\n⚠️ <b>تنبيه:</b> هذا المنتج يحتاج تحقق من المكونات"

        # ✅ أزرار تفاعلية مع زر الإبلاغ عن خطأ
        keyboard = [
            [
                InlineKeyboardButton("💾 حفظ في المفضلة", callback_data=f"save_{name}"),
                InlineKeyboardButton("📤 مشاركة النتيجة", callback_data=f"share_{name}")
            ],
            [
                InlineKeyboardButton("🔄 اقترحي لي بدائل", callback_data=f"alt_{name}"),
                InlineKeyboardButton("⚠️ إبلاغ عن خطأ", callback_data=f"report_prod_{name}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # إرسال الصورة أولاً (إن وجدت)
        # في دالة handle_message، استبدل جزء إرسال الصورة بهذا:
        # إرسال الصورة أولاً (إن وجدت)
        # ✅ إرسال الصورة مع العلامة المائية
        if image_url:
            try:
                from backend.watermark import watermarker
                from PIL import ImageFile
                ImageFile.LOAD_TRUNCATED_IMAGES = True

                # محاولة إضافة علامة مائية
                watermarked_img = watermarker.add_watermark(image_url)

                if watermarked_img:
                    # إرسال الصورة من الذاكرة
                    await update.message.reply_photo(
                        photo=watermarked_img,
                        caption=f"🛍️ <b>{name}</b>\n<i>🔒 محمي بحلالية</i>",
                        parse_mode="HTML"
                    )
                else:
                    # إذا فشل، أرسل الرابط العادي
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=f"🛍️ <b>{name}</b>",
                        parse_mode="HTML"
                    )

            except Exception as e:
                logger.warning(f"فشل الصورة المائية، إرسال عادي: {e}")
                # Fallback: إرسال عادي
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"🛍️ <b>{name}</b>",
                    parse_mode="HTML"
                )

                # إذا كانت النتيجة مسار محلي (وليس رابط)
                if os.path.exists(watermarked_path):
                    with open(watermarked_path, "rb") as photo_file:
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=f"️ <b>{name}</b>",
                            parse_mode="HTML"
                        )
                    # حذف الملف المؤقت بعد الإرسال
                    try:
                        os.remove(watermarked_path)
                    except:
                        pass
                else:
                    # إذا فشل المعالجة، أرسل الرابط الأصلي
                    await update.message.reply_photo(
                        photo=watermarked_path,
                        caption=f"️ <b>{name}</b>",
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.warning(f"فشل إرسال الصورة المائية: {e}")
                # Fallback: إرسال الصورة من الرابط مباشرة
                try:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=f"🛍️ <b>{name}</b>",
                        parse_mode="HTML"
                    )
                except:
                    pass
        # إرسال الرسالة النصية
        await update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        try:
            await status_msg.edit_text(" عذراً، حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.")
        except:
            await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار التفاعلية"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # زر "حللي لي منتجاً الآن" من شاشة البداية
    if data == "start_analyze":
        await query.edit_message_text(
            "🔍 <b>اكتبي اسم المنتج الذي تريدين تحليله</b>\n\n"
            "مثال:\n"
            "• خلاط محمول\n"
            "• عطر نسائي فاخر\n"
            "• كريم بشرة طبيعي\n\n"
            "وسأقوم بتحليله فوراً مع فحص المكونات الحلال!",
            parse_mode="HTML"
        )

    # زر "أفضل المنتجات"
    elif data == "show_top":
        try:
            from backend.database import get_top_products
            products = get_top_products(limit=5)

            if not products:
                await query.edit_message_text("📭 لا توجد منتجات موصى بها حالياً.")
                return

            message = "🏆 <b>أفضل المنتجات الموصى بها:</b>\n\n"
            for i, p in enumerate(products[:5], 1):
                p = dict(p)
                name = p.get("product_name", "غير محدد")
                score = p.get("score", 0)
                rec = p.get("recommendation", "موصى به")
                message += f"{i}. <b>{name}</b>\n"
                message += f"   🤖 الثقة: {score}/10\n"
                message += f"    {rec}\n\n"

            message += "💡 <b>اكتبي اسم أي منتج لتحليله بالتفصيل!</b>"
            await query.edit_message_text(message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error in show_top: {e}")
            await query.edit_message_text("❌ حدث خطأ في جلب المنتجات.")

    # زر "دليل الحلال والثقة"
    elif data == "halal_guide_btn":
        message = (
            "🕌 <b>منهجية حلالية في ضمان النقاء والثقة</b>\n\n"
            "نحن في حلالية نؤمن بأن التسوق الآمن حق لكل امرأة. لذلك، قمنا ببناء محرك فحص ذكي يعتمد على:\n\n"
            "🟢 <b>حلال (موثوق):</b>\n"
            "لا يحتوي على أي مكونات محرمة أو مشتقات حيوانية مشبوهة.\n\n"
            "🟡 <b>يحتاج تحقق (مختلف عليه):</b>\n"
            "قد يحتوي على مكونات مثل (الجيلاتين، الغليسيرين الحيواني، الكارمين). ننصحك بمراجعة الشركة المصنعة للتأكد من مصدرها.\n\n"
            " <b>غير حلال (مرفوض):</b>\n"
            "يحتوي بشكل قاطع على (كحول إيثيلي، دهون خنزير، مشتقاته، أو إنزيمات حيوانية محرمة).\n\n"
            "⚖️ <b>مصادرنا:</b>\n"
            "نعتمد في تصنيفنا على قوائم مكونات معتمدة من هيئات رقابية عالمية، ونقوم بالتحديث المستمر.\n\n"
            "💡 <b>نصيحة:</b> إذا شككتِ في أي منتج، استخدمي أمر /report لإبلاغنا وسنراجعه فوراً."
        )
        await query.edit_message_text(message, parse_mode="HTML")

    # زر "اختيار اليوم"
    elif data == "daily_pick_btn":
        try:
            from backend.database import get_top_products
            products = get_top_products(limit=5)

            if not products:
                await query.edit_message_text("📭 لا توجد منتجات مقترحة حالياً.")
                return

            import random
            pick = random.choice([dict(p) for p in products])

            message = (
                f"🎁 <b>اختيار حلالية لكِ اليوم!</b>\n\n"
                f"🛍️ <b>{pick['product_name']}</b>\n"
                f"⭐ التقييم: {pick.get('rating', 4.5)}/5\n"
                f"🤖 درجة الثقة: {pick.get('score', 8)}/10\n"
                f"💰 السعر التقريبي: ${pick.get('sell_price', 0)}\n\n"
                f"💡 {pick.get('recommendation', 'منتج ممتاز')}\n\n"
                f"اكتبي اسم هذا المنتج في المحادثة لتحليله وتفصيل مكوناته! 👇"
            )
            await query.edit_message_text(message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error in daily_pick: {e}")
            await query.edit_message_text("❌ حدث خطأ في جلب الاقتراح.")

    # زر "ملفي الشخصي"
    elif data == "my_profile":
        await query.edit_message_text(
            "👤 <b>لعرض ملفك الشخصي، استخدمي الأمر:</b>\n\n"
            "<code>/profile</code>\n\n"
            "ستجدين فيه:\n"
            "• شارتكِ الحالية\n"
            "• نقاطكِ ومستواكِ\n"
            "• إحصائيات نشاطكِ\n"
            "• آخر الأنشطة",
            parse_mode="HTML"
        )

    # زر "المفضلة"
    elif data == "my_favorites":
        await query.edit_message_text(
            "💾 <b>لعرض منتجاتك المفضلة، استخدمي الأمر:</b>\n\n"
            "<code>/favorites</code>\n\n"
            "وللحفظ: <code>/save اسم المنتج</code>\n"
            "وللحذف: <code>/unsave اسم المنتج</code>",
            parse_mode="HTML"
        )

    # زر "حفظ في المفضلة" (من تحليل المنتج)
    elif data.startswith("save_"):
        product_name = data.replace("save_", "")
        try:
            await query.edit_message_text(
                f"💾 لحفظ <b>{product_name}</b>، يرجى استخدام الأمر:\n"
                f"<code>/save {product_name}</code>\n"
                f"(هذا يضمن حفظ البيانات الكاملة)",
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text("❌ حدث خطأ أثناء الحفظ.")

    # زر "مشاركة النتيجة"
    elif data.startswith("share_"):
        product_name = data.replace("share_", "")
        await query.edit_message_text(
            f" <b>لمشاركة تحليل {product_name}:</b>\n\n"
            f"اضغطي على زر 'مشاركة' في رسالة التحليل، أو انسخي النص وأرسليه لصديقاتكِ.",
            parse_mode="HTML"
        )

    # زر "اقترحي لي بدائل"
    elif data.startswith("alt_"):
        product_name = data.replace("alt_", "")
        await query.edit_message_text(
            f"🔄 <b>البحث عن بدائل لـ: {product_name}</b>\n\n"
            f"💡 <b>نصيحة:</b> استخدمي الأمر:\n"
            f"<code>/compare {product_name} vs [اسم بديل معروف]</code>\n\n"
            f"أو اكتبي اسم فئة المنتج (مثال: 'خلاط زجاجي') للحصول على توصيات جديدة.",
            parse_mode="HTML"
        )

    # ✅ زر "إبلاغ عن خطأ" (من تحليل المنتج)
    elif data.startswith("report_prod_"):
        product_name = data.replace("report_prod_", "")
        await query.edit_message_text(
            f"⚠️ <b>الإبلاغ عن مشكلة في: {product_name}</b>\n\n"
            f"استخدمي الأمر:\n"
            f"<code>/report مشكلة في {product_name} - [تفاصيل المشكلة]</code>\n\n"
            f"مثال:\n"
            f"<code>/report مشكلة في عطر فاخر - يحتوي على كحول رغم ادعاء الحلال</code>\n\n"
            f"فريق حلالية سيراجع البلاغ خلال 24 ساعة.",
            parse_mode="HTML"
        )

    else:
        await query.edit_message_text("⚠️ إجراء غير معروف.")