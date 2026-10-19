"""
حلالية - منصة الذكاء الاصطناعي الحلال للمتسوقات
Command Handlers - النسخة النهائية
"""

import logging
import json
import requests
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram_bot.config import BASE_URL
from backend.db import db

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🌸 أهلاً وسهلاً بكِ في حلالية\n\n"
        "منصة الذكاء الاصطناعي الحلال لمساعدتكِ في التسوق الذكي والآمن\n\n"
        "نحن هنا لنقدم لكِ:\n"
        "✅ تحليلات موثوقة للمنتجات\n"
        "✅ مقارنات ذكية بين الخيارات\n"
        "✅ فحص دقيق للمكونات الحلال\n"
        "✅ نصائح تسوق تتوافق مع القيم\n\n"
        "كيف تستخدمين حلالية؟\n"
        "1️⃣ اكتبي اسم أي منتج (مثال: خلاط محمول)\n"
        "2️⃣ للمقارنة: /compare منتج 1 vs منتج 2\n\n"
        "الأوامر المتاحة:\n"
        "/start - رسالة الترحيب\n"
        "/help - دليل المساعدة\n"
        "/halal_guide - دليل الحلال والثقة\n"
        "/daily - اختيار اليوم المميز\n"
        "/stats - إحصائيات البحث\n"
        "/top - أفضل المنتجات الموصى بها\n"
        "/save [اسم المنتج] - حفظ في المفضلة\n"
        "/favorites - عرض المفضلة\n"
        "/unsave [اسم المنتج] - حذف من المفضلة\n"
        "/delete [اسم المنتج] - حذف من السجل\n"
        "/alternatives [فئة المنتج] - اقتراح بدائل ذكية\n"
        "/alert [منتج] [سعر] - تنبيه عند انخفاض السعر\n"
        "/myalerts - عرض تنبيهاتكِ النشطة\n"
        "/category [اسم الفئة] - تصفح المنتجات حسب الفئة\n"
        "/gifts [المناسبة] - اقتراحات هدايا ذكية\n"
        "/wishlist - إدارة قوائم الرغبات\n"
        "/review [منتج] [تقييم] - تقييم منتج\n"
        "/myreviews - عرض تقييماتكِ\n"
        "/profile - ملفكِ الشخصي والنقاط\n"
        "/report [تفاصيل المشكلة] - الإبلاغ عن مشكلة"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔍 حللي لي منتجاً الآن", callback_data="start_analyze"),
            InlineKeyboardButton("🏆 أفضل المنتجات", callback_data="show_top")
        ],
        [
            InlineKeyboardButton("📋 دليل الحلال والثقة", callback_data="halal_guide_btn"),
            InlineKeyboardButton("🎁 اختيار اليوم", callback_data="daily_pick_btn")
        ],
        [
            InlineKeyboardButton("👤 ملفي الشخصي", callback_data="my_profile"),
            InlineKeyboardButton("💾 المفضلة", callback_data="my_favorites")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "📖 دليل استخدام حلالية\n\n"
        "الأوامر الرئيسية:\n"
        "/start - رسالة الترحيب\n"
        "/help - هذا الدليل\n"
        "/halal_guide - دليل الحلال والثقة\n"
        "/daily - اختيار اليوم المميز\n"
        "/stats - إحصائيات البحث\n"
        "/top - أفضل المنتجات الموصى بها\n\n"
        "المفضلة:\n"
        "/save [اسم المنتج] - حفظ في المفضلة\n"
        "/favorites - عرض المنتجات المفضلة\n"
        "/unsave [اسم المنتج] - حذف من المفضلة\n\n"
        "المقارنة:\n"
        "/compare منتج 1 vs منتج 2 - مقارنة ذكية\n\n"
        "إدارة السجل:\n"
        "/delete [اسم المنتج] - حذف من سجل البحث\n\n"
        "البدائل:\n"
        "/alternatives [فئة المنتج] - اقتراح بدائل ذكية\n\n"
        "الإبلاغ:\n"
        "/report [تفاصيل المشكلة] - الإبلاغ عن مشكلة\n\n"
        "تنبيهات الأسعار:\n"
        "/alert [منتج] [سعر] - تنبيه عند انخفاض السعر\n"
        "/myalerts - عرض تنبيهاتكِ النشطة\n"
        "/cancelalert [منتج] - إلغاء تنبيه سعر\n\n"
        "الفئات والهدايا:\n"
        "/category [اسم الفئة] - تصفح المنتجات حسب الفئة\n"
        "/gifts [المناسبة] - اقتراحات هدايا ذكية\n\n"
        "قوائم الرغبات:\n"
        "/wishlist - عرض جميع القوائم\n"
        "/wishlist new [اسم] - إنشاء قائمة جديدة\n"
        "/wishlist add [رقم] [منتج] - إضافة منتج\n"
        "/wishlist view [رقم] - عرض محتوى القائمة\n\n"
        "التقييمات:\n"
        "/review [منتج] [تقييم] [تعليق] - تقييم منتج\n"
        "/reviews [منتج] - عرض تقييمات منتج\n"
        "/myreviews - عرض تقييماتكِ\n"
        "/unreview [منتج] - حذف تقييمكِ\n\n"
        "نصائح:\n"
        "• اكتبي اسم أي منتج لتحليله فوراً\n"
        "• استخدمي /compare للمقارنة بين خيارين\n"
        "• احفظي منتجاتكِ المفضلة بـ /save"
    )
    await update.message.reply_text(message)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{BASE_URL}/saved", timeout=10)
        if response.status_code != 200:
            await update.message.reply_text(" عذراً، حدث خطأ في الاتصال.")
            return

        products = response.json()
        if not isinstance(products, list) or not products:
            await update.message.reply_text("📊 لا توجد منتجات في سجل البحث بعد.")
            return

        total = len(products)
        best = max((p for p in products if isinstance(p, dict)), key=lambda x: x.get("score", 0), default={})

        message = (
            f"📊 إحصائيات حلالية\n\n"
            f"️ إجمالي المنتجات التي بحثتِ عنها: {total}\n"
            f"🏆 أعلى منتج حصل على توصية: {best.get('product_name', 'غير محدد')} (بدرجة ثقة {best.get('score', 0)}/10)\n"
        )
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in stats_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{BASE_URL}/hunt", timeout=10)
        if response.status_code != 200:
            await update.message.reply_text("❌ عذراً، حدث خطأ في الاتصال.")
            return

        products = response.json()
        if not isinstance(products, list) or not products:
            await update.message.reply_text("🔥 لا توجد منتجات موصى بها حالياً.")
            return

        message = "🌟 أفضل المنتجات الموصى بها من حلالية:\n\n"
        for i, p in enumerate(products[:5], 1):
            if isinstance(p, dict):
                name = p.get("product_name", "غير محدد")
                rec = p.get("recommendation", "موصى به")
                message += f"{i}. {name}\n    {rec}\n\n"

        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in top_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "⚠️ يرجى كتابة اسم المنتج بعد الأمر.\nمثال: /delete خلاط محمول"
            )
            return

        product_name = " ".join(context.args).strip().lower()

        response = requests.get(f"{BASE_URL}/saved", timeout=10)
        if response.status_code != 200:
            await update.message.reply_text("❌ عذراً، حدث خطأ في الاتصال.")
            return

        products = response.json()
        if not isinstance(products, list) or not products:
            await update.message.reply_text("📭 سجل البحث فارغ.")
            return

        found = False
        updated_products = []

        for p in products:
            if isinstance(p, dict):
                name = p.get("product_name", "").lower()
                if name == product_name:
                    found = True
                else:
                    updated_products.append(p)
            else:
                updated_products.append(p)

        if not found:
            await update.message.reply_text(f"❌ لم يتم العثور على '{product_name}' في السجل.")
            return

        db_path = Path(__file__).parent.parent / "backend" / "products_db.json"
        if db_path.exists():
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(updated_products, f, ensure_ascii=False, indent=4)

        await update.message.reply_text(f"✅ تم حذف {product_name} من سجل البحث بنجاح.")
    except Exception as e:
        logger.error(f"Error in delete_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "⚖️ كيف تقارنين في حلالية؟\n"
                "اكتبي الأمر متبوعاً باسم المنتجين وكلمة vs أو مقابل.\n\n"
                "مثال: /compare خلاط محمول vs خلاط زجاجي\n"
                "مثال: /compare عطر زارا مقابل عطر هوجو بوس"
            )
            return

        full_text = " ".join(context.args)
        split_pattern = r'\s+(?:vs|مقابل|و)\s+'
        parts = re.split(split_pattern, full_text, flags=re.IGNORECASE)

        if len(parts) != 2:
            await update.message.reply_text(
                "⚠️ لم أستطع تمييز المنتجين. يرجى استخدام كلمة vs أو مقابل بينهما.\n"
                "مثال: /compare منتج 1 vs منتج 2"
            )
            return

        product1 = parts[0].strip()
        product2 = parts[1].strip()

        await update.message.reply_text(f"⏳ جاري التحليل والمقارنة في حلالية:\n1️⃣ {product1}\n2️ {product2}...")

        res1 = requests.post(f"{BASE_URL}/analyze", json={"product_name": product1}, timeout=15)
        res2 = requests.post(f"{BASE_URL}/analyze", json={"product_name": product2}, timeout=15)

        if res1.status_code != 200 or res2.status_code != 200:
            await update.message.reply_text("❌ عذراً، حدث خطأ أثناء جلب بيانات أحد المنتجات.")
            return

        data1 = res1.json()
        data2 = res2.json()

        if "error" in data1 or "error" in data2:
            await update.message.reply_text("❌ عذراً، لم أتمكن من تحليل أحد الاسمين. يرجى التأكد من كتابة الأسماء بشكل واضح.")
            return

        def format_product(p):
            name = p.get("product_name", "غير محدد")
            score = p.get("score", 0)
            rec = p.get("recommendation", "موصى به")
            price = p.get("sell_price", 0)
            rating = p.get("rating", 0)
            reviews = p.get("reviews", 0)

            if score >= 7:
                trust = "🌟 موثوق وعالي الجودة"
            elif score >= 5:
                trust = "✅ جيد ومناسب"
            else:
                trust = "⚠️ يحتاج لمراجعة إضافية"

            return (
                f"️ {name}\n"
                f"💰 السعر التقريبي: ${price}\n"
                f"⭐ التقييم: {rating}/5 (من {reviews} تقييم)\n"
                f"🤖 درجة الثقة: {score}/10\n"
                f"💡 حكم حلالية: {trust}\n"
                f"🎯 التوصية: {rec}"
            )

        msg1 = format_product(data1)
        msg2 = format_product(data2)

        message = (
            f"⚖️ مقارنة حلالية الذكية\n\n"
            f"--- المنتج الأول ---\n"
            f"{msg1}\n\n"
            f"--- المنتج الثاني ---\n"
            f"{msg2}\n\n"
            f" نصيحة حلالية: اختاري المنتج الذي يحصل على 'موثوق وعالي الجودة' ويلائم ميزانيتكِ واحتياجكِ الحقيقي، مع مراعاة القيم والجودة."
        )

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in compare_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع أثناء المقارنة.")


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "⚠️ يرجى كتابة اسم المنتج بعد الأمر.\nمثال: /save خلاط محمول"
        )
        return

    product_name = " ".join(context.args).strip()

    try:
        response = requests.get(f"{BASE_URL}/saved", timeout=10)
        if response.status_code != 200:
            await update.message.reply_text("❌ عذراً، حدث خطأ في الاتصال.")
            return

        products = response.json()
        product_data = None

        for p in products:
            if isinstance(p, dict) and p.get("product_name", "").lower() == product_name.lower():
                product_data = p
                break

        if not product_data:
            await update.message.reply_text(f"❌ لم يتم العثور على '{product_name}' في السجل. يرجى تحليله أولاً.")
            return

        from telegram_bot.favorites import add_favorite
        success = add_favorite(user_id, product_data)

        if success:
            from backend.points import add_points
            add_points(user_id, "save", f"حفظ {product_name}")
            await update.message.reply_text(f"✅ تم حفظ {product_name} في المفضلة.")
        else:
            await update.message.reply_text(f"⚠️ {product_name} موجود بالفعل في المفضلة.")
    except Exception as e:
        logger.error(f"Error in save_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    try:
        from telegram_bot.favorites import get_user_favorites
        favorites = get_user_favorites(user_id)

        if not favorites:
            await update.message.reply_text("📭 المفضلة فارغة. استخدمي /save [اسم المنتج] لإضافة منتجات.")
            return

        message = "⭐ المنتجات المفضلة:\n\n"
        for i, fav in enumerate(favorites[:10], 1):
            name = fav.get("product_name", "غير محدد")
            score = fav.get("score", 0)
            message += f"{i}. {name} (درجة الثقة: {score}/10)\n"

        message += f"\n📊 الإجمالي: {len(favorites)} منتج"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in favorites_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def unsave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "️ يرجى كتابة اسم المنتج بعد الأمر.\nمثال: /unsave خلاط محمول"
        )
        return

    product_name = " ".join(context.args).strip()

    try:
        from telegram_bot.favorites import remove_favorite
        success = remove_favorite(user_id, product_name)

        if success:
            await update.message.reply_text(f"✅ تم حذف {product_name} من المفضلة.")
        else:
            await update.message.reply_text(f"❌ لم يتم العثور على '{product_name}' في المفضلة.")
    except Exception as e:
        logger.error(f"Error in unsave_command: {e}", exc_info=True)
        await update.message.reply_text(" عذراً، حدث خطأ غير متوقع.")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "⚠️ يرجى كتابة تفاصيل المشكلة بعد الأمر.\n"
                "مثال: /report منتج خلاط محمول يحتوي على معلومات خاطئة\n\n"
                "أو يمكنكِ الإبلاغ عن:\n"
                "• معلومات غير دقيقة\n"
                "• منتج مشبوه\n"
                "• خطأ في التحليل\n"
                "• اقتراح تحسين"
            )
            return

        report_text = " ".join(context.args).strip()
        user_id = update.effective_user.id
        username = update.effective_user.username or "مجهول"

        report_path = Path(__file__).parent.parent / "backend" / "reports.json"

        reports = []
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                reports = json.load(f)

        new_report = {
            "user_id": user_id,
            "username": username,
            "text": report_text,
            "timestamp": str(Path(__file__).parent.parent / "backend" / "reports.json")
        }

        reports.append(new_report)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=4)

        await update.message.reply_text(
            f"✅ شكراً لكِ! تم تسجيل بلاغكِ بنجاح.\n\n"
            f"سيتابع فريق حلالية البلاغ خلال 24 ساعة.\n"
            f"رقم البلاغ: #{len(reports)}"
        )
    except Exception as e:
        logger.error(f"Error in report_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def alternatives_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "🔄 يرجى كتابة فئة المنتج أو اسم المنتج العام.\n"
                "مثال: <code>/alternatives خلاط</code>\n"
                "مثال: <code>/alternatives غسالة وجه</code>",
                parse_mode="HTML"
            )
            return

        category = " ".join(context.args).strip()
        await update.message.reply_text(f"⏳ جاري البحث عن أفضل البدائل لفئة: {category}...")

        response = requests.get(f"{BASE_URL}/hunt", timeout=10)
        if response.status_code != 200:
            await update.message.reply_text(" عذراً، حدث خطأ في الاتصال.")
            return

        products = response.json()
        if not isinstance(products, list) or not products:
            await update.message.reply_text("📭 لا توجد توصيات متاحة حالياً.")
            return

        filtered = [p for p in products if category.lower() in p.get("product_name", "").lower()]

        if not filtered:
            filtered = products[:3]
            intro = f"🌸 لم نجد نتائج دقيقة لـ '{category}'، ولكن إليك أفضل توصيات حلالية العامة:"
        else:
            intro = f" أفضل البدائل الموصى بها لفئة <b>{category}</b>:"

        message = f"{intro}\n\n"
        for i, p in enumerate(filtered[:3], 1):
            name = p.get("product_name", "غير محدد")
            score = p.get("score", 0)
            price = p.get("sell_price", 0)
            rec = p.get("recommendation", "موصى به")
            message += f"{i}. <b>{name}</b>\n"
            message += f"   💰 السعر: ${price} | 🤖 الثقة: {score}/10\n"
            message += f"   💡 {rec}\n\n"

        message += "💡 <b>نصيحة حلالية:</b> قارني بين هذه الخيارات باستخدام أمر /compare قبل الشراء."

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in alternatives_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def process_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "⚠️ طريقة الاستخدام:\n"
                "<code>/alert اسم_المنتج السعر_المستهدف</code>\n\n"
                "مثال: <code>/alert خلاط محمول 50</code>",
                parse_mode="HTML"
            )
            return

        target_price_str = context.args[-1]
        try:
            target_price = float(target_price_str)
        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال سعر صحيح (أرقام فقط).")
            return

        product_name = " ".join(context.args[:-1]).strip()
        user_id = update.effective_user.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name

        from telegram_bot.favorites import get_or_create_user
        get_or_create_user(user_id, username, first_name)

        from backend.alerts import create_price_alert
        success, status, data = create_price_alert(user_id, product_name, target_price)

        if not success:
            await update.message.reply_text(
                f"❌ فشل إعداد التنبيه: {data}\nتأكدي من تحليل المنتج أولاً باستخدام اسمه."
            )
            return

        if status == "already_lower":
            await update.message.reply_text(
                f"🎉 خبر سار! سعر <b>{product_name}</b> الحالي هو {data}$، وهو بالفعل أقل من أو يساوي ميزانيتكِ ({target_price}$)!\n\n"
                "هل تريدين تحليله مرة أخرى؟ اكتبي اسمه.",
                parse_mode="HTML"
            )
        elif status == "updated":
            await update.message.reply_text(
                f"✅ تم تحديث تنبيهكِ لـ <b>{product_name}</b>.\n"
                f"سنخبركِ عندما ينخفض السعر إلى {data}$ أو أقل.",
                parse_mode="HTML"
            )
        else:
            from backend.points import add_points
            add_points(user_id, "alert", f"تنبيه سعر لـ {product_name}")
            await update.message.reply_text(
                f"✅ تم حفظ التنبيه بنجاح!\n\n"
                f"📦 المنتج: <b>{product_name}</b>\n"
                f"🎯 سنخبركِ عندما ينخفض السعر إلى: <b>{data}$</b> أو أقل.\n\n"
                f"يمكنكِ مراجعة تنبيهاتكِ باستخدام أمر: <code>/myalerts</code>",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error in process_alert: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def myalerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        from backend.alerts import get_user_alerts
        alerts = get_user_alerts(user_id)

        if not alerts:
            await update.message.reply_text(
                "📭 لا توجد تنبيهات أسعار نشطة حالياً.\nاستخدمي <code>/alert منتج سعر</code> لإضافة واحد.",
                parse_mode="HTML"
            )
            return

        message = "🔔 <b>تنبيهات الأسعار النشطة:</b>\n\n"
        for i, alert in enumerate(alerts[:10], 1):
            name = alert.get("product_name", "غير محدد")
            target = alert.get("target_price", 0)
            current = alert.get("current_price", 0)
            message += f"{i}. <b>{name}</b>\n"
            message += f"   🎯 السعر المستهدف: {target}$ | 💰 السعر الحالي: {current}$\n\n"

        message += "💡 <b>نصيحة:</b> لحذف تنبيه، استخدمي: <code>/cancelalert اسم_المنتج</code>"

        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in myalerts_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def cancelalert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "⚠️ يرجى كتابة اسم المنتج بعد الأمر.\nمثال: <code>/cancelalert خلاط محمول</code>",
                parse_mode="HTML"
            )
            return

        product_name = " ".join(context.args).strip()
        user_id = update.effective_user.id

        from backend.alerts import delete_alert
        success = delete_alert(user_id, product_name)

        if success:
            await update.message.reply_text(f"✅ تم إلغاء تنبيه السعر لـ: <b>{product_name}</b>.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"❌ لم يتم العثور على تنبيه نشط لـ: <b>{product_name}</b>.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in cancelalert_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "🏷️ يرجى كتابة اسم الفئة.\n\n"
                "الفئات المتاحة:\n"
                "• عطور\n• مكياج\n• عناية بالبشرة\n• أزياء\n• أدوات منزلية\n• إلكترونيات\n• أطفال",
                parse_mode="HTML"
            )
            return

        category_name = " ".join(context.args).strip().lower()
        await update.message.reply_text(f"⏳ جاري البحث في فئة: <b>{category_name}</b>...", parse_mode="HTML")

        synonyms = {
            "عطور": ["عطر", "عطور", "برفان", "fragrance", "perfume"],
            "مكياج": ["مكياج", "كوزمتكس", "makeup", "cosmetics"],
            "بشرة": ["بشرة", "skin", "كريم", "سيروم", "غسول"],
            "شعر": ["شعر", "hair", "شامبو", "بلسم"],
            "منزل": ["منزل", "مطبخ", "home", "kitchen", "ذكي"],
            "إلكترونيات": ["إلكترونيات", "electronics", "سماعة", "سماعات", "لاسلكي"],
            "أطفال": ["أطفال", "kids", "baby", "لعبة"]
        }

        search_keywords = []
        if category_name in synonyms:
            search_keywords = synonyms[category_name]
        else:
            search_keywords = [category_name]

        conditions = " OR ".join([
            "LOWER(product_name) LIKE %s",
            "LOWER(niche) LIKE %s"
        ] * len(search_keywords))

        query = f"""
            SELECT product_name, score, sell_price, recommendation, niche 
            FROM products 
            WHERE {conditions}
            ORDER BY score DESC 
            LIMIT 5
        """

        params = []
        for kw in search_keywords:
            params.extend([f"%{kw}%", f"%{kw}%"])

        results = db.execute_query(query, tuple(params), fetch=True)

        if not results:
            await update.message.reply_text(
                f"📭 لم نجد منتجات مطابقة لفئة '{category_name}' حالياً.\n"
                f"جرّبي فئة أخرى أو اكتبي اسم منتج محدد لتحليله.",
                parse_mode="HTML"
            )
            return

        message = f"🌟 أفضل المنتجات في فئة <b>{category_name}</b>:\n\n"
        for i, row in enumerate(results, 1):
            name = row.get("product_name", "غير محدد")
            score = row.get("score", 0)
            price = row.get("sell_price", 0)
            rec = row.get("recommendation", "موصى به")

            icon = "✅" if "ممتاز" in str(rec) or "جيد" in str(rec) else "⚠️"

            message += f"{i}. <b>{name}</b>\n"
            message += f"   💰 السعر: ${price} | 🤖 الثقة: {score}/10\n"
            message += f"   {icon} {rec}\n\n"

        message += " <b>نصيحة حلالية:</b> يمكنكِ مقارنة أي منتجين باستخدام أمر: \n<code>/compare منتج 1 vs منتج 2</code>"

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in category_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع أثناء البحث.")


async def gifts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "🎁 دليل الهدايا الذكي من حلالية\n\n"
                "اكتبي المناسبة وسأقترح لكِ أفضل الهدايا:\n\n"
                "• <code>/gifts عيد الأم</code>\n"
                "• <code>/gifts عروس</code>\n"
                "• <code>/gifts صديقة</code>\n"
                "• <code>/gifts مولود جديد</code>\n"
                "• <code>/gifts منزل</code>",
                parse_mode="HTML"
            )
            return

        occasion = " ".join(context.args).strip().lower()
        await update.message.reply_text(f"⏳ جاري تحضير اقتراحات الهدايا لـ: <b>{occasion}</b>...", parse_mode="HTML")

        occasion_keywords = {
            "عيد الأم": ["عطر", "كريم", "بشرة", "شعر", "هدية", "فاخر"],
            "عروس": ["مكياج", "عطر", "فاخر", "أصلي", "عناية"],
            "صديقة": ["محمول", "صغير", "مطبخ", "منزل", "أكسسوار"],
            "مولود جديد": ["أطفال", "لعبة", "بيبي"],
            "منزل": ["منزل", "مطبخ", "ذكي", "أداة"]
        }

        keywords_to_search = []
        for key, words in occasion_keywords.items():
            if key in occasion:
                if isinstance(words, list):
                    keywords_to_search.extend(words)
                else:
                    keywords_to_search.append(words)

        if not keywords_to_search:
            keywords_to_search = [occasion]

        conditions = " OR ".join(["LOWER(product_name) LIKE %s"] * len(keywords_to_search))
        query = f"""
            SELECT product_name, score, sell_price, recommendation 
            FROM products 
            WHERE {conditions}
            ORDER BY score DESC 
            LIMIT 4
        """
        params = tuple(f"%{kw}%" for kw in keywords_to_search)
        results = db.execute_query(query, params, fetch=True)

        if not results:
            await update.message.reply_text(
                f" لم نجد اقتراحات محددة لـ '{occasion}' في قاعدة البيانات حالياً.\n"
                f"جرّبي تحليل منتج معين تظنين أنه مناسب، وسأساعدكِ في تقييمه!",
                parse_mode="HTML"
            )
            return

        message = f"🎁 <b>أفضل اقتراحات الهدايا لـ: {occasion}</b>\n\n"
        for i, row in enumerate(results, 1):
            name = row.get("product_name", "غير محدد")
            score = row.get("score", 0)
            price = row.get("sell_price", 0)
            rec = row.get("recommendation", "موصى به")

            message += f"{i}. 🎀 <b>{name}</b>\n"
            message += f"   💰 السعر التقريبي: ${price} | 🤖 درجة الثقة: {score}/10\n"
            message += f"   💡 {rec}\n\n"

        message += " <b>نصيحة:</b> لحفظ أي من هذه الهدايا لشرائها لاحقاً، استخدمي:\n<code>/save اسم المنتج</code>"

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in gifts_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع أثناء تحضير الاقتراحات.")


async def wishlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if not context.args:
            from backend.wishlists import get_user_wishlists
            wishlists = get_user_wishlists(user_id)

            if not wishlists:
                await update.message.reply_text(
                    "📋 <b>قوائم الرغبات</b>\n\n"
                    "لم تنشئ أي قائمة بعد.\n\n"
                    "🆕 لإنشاء قائمة جديدة:\n"
                    "<code>/wishlist new اسم القائمة</code>\n\n"
                    "مثال: <code>/wishlist new قائمة العروسة</code>",
                    parse_mode="HTML"
                )
                return

            message = "📋 <b>قوائم الرغبات الخاصة بكِ:</b>\n\n"
            for i, wl in enumerate(wishlists[:10], 1):
                name = wl.get("name", "بدون اسم")
                count = wl.get("items_count", 0)
                desc = wl.get("description", "")
                message += f"{i}. <b>{name}</b> ({count} منتج)\n"
                if desc:
                    message += f"   📝 {desc}\n"
                message += f"   🔗 المعرف: <code>{wl['id']}</code>\n\n"

            message += (
                "💡 <b>الأوامر المتاحة:</b>\n"
                "• إنشاء: <code>/wishlist new اسم القائمة</code>\n"
                "• إضافة منتج: <code>/wishlist add رقم_القائمة اسم المنتج</code>\n"
                "• عرض: <code>/wishlist view رقم القائمة</code>\n"
                "• حذف: <code>/wishlist delete رقم القائمة</code>"
            )

            await update.message.reply_text(message, parse_mode="HTML")
            return

        action = context.args[0].lower()

        if action == "new":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "⚠️ يرجى كتابة اسم القائمة.\n"
                    "مثال: <code>/wishlist new قائمة العروسة</code>",
                    parse_mode="HTML"
                )
                return

            list_name = " ".join(context.args[1:]).strip()
            from backend.wishlists import create_wishlist
            success, data = create_wishlist(user_id, list_name)

            if success:
                from backend.points import add_points
                add_points(user_id, "wishlist_create", f"إنشاء قائمة {list_name}")
                await update.message.reply_text(
                    f"✅ تم إنشاء قائمة '<b>{list_name}</b>' بنجاح!\n\n"
                    f"🔗 المعرف: <code>{data}</code>\n"
                    f" أضيفي منتجات باستخدام:\n"
                    f"<code>/wishlist add {data} اسم المنتج</code>",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(f"❌ فشل إنشاء القائمة: {data}")

        elif action == "add":
            if len(context.args) < 3:
                await update.message.reply_text(
                    "⚠️ طريقة الاستخدام:\n"
                    "<code>/wishlist add رقم_القائمة اسم المنتج</code>\n\n"
                    "مثال: <code>/wishlist add 1 خلاط محمول</code>",
                    parse_mode="HTML"
                )
                return

            try:
                wishlist_id = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ رقم القائمة يجب أن يكون رقماً.")
                return

            product_name = " ".join(context.args[2:]).strip()
            from backend.wishlists import add_to_wishlist
            success, data = add_to_wishlist(user_id, wishlist_id, product_name)

            if success:
                from backend.points import add_points
                add_points(user_id, "wishlist_add", f"إضافة {product_name} للقائمة")
                await update.message.reply_text(
                    f"✅ تم إضافة '<b>{product_name}</b>' إلى القائمة رقم {wishlist_id}.",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(f"❌ {data}")

        elif action == "view":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "⚠️ يرجى كتابة رقم القائمة.\n"
                    "مثال: <code>/wishlist view 1</code>",
                    parse_mode="HTML"
                )
                return

            try:
                wishlist_id = int(context.args[1])
            except ValueError:
                await update.message.reply_text(" رقم القائمة يجب أن يكون رقماً.")
                return

            from backend.wishlists import get_wishlist_items
            result = get_wishlist_items(user_id, wishlist_id)

            if not result:
                await update.message.reply_text("❌ القائمة غير موجودة أو لا تملكينها.")
                return

            wl = result["wishlist"]
            items = result["items"]

            message = f"📋 <b>{wl['name']}</b>\n"
            if wl.get('description'):
                message += f"📝 {wl['description']}\n"
            message += f"📊 عدد المنتجات: {len(items)}\n\n"

            if not items:
                message += "📭 القائمة فارغة. أضيفي منتجات باستخدام:\n"
                message += f"<code>/wishlist add {wishlist_id} اسم المنتج</code>"
            else:
                for i, item in enumerate(items[:10], 1):
                    name = item.get("product_name", "غير محدد")
                    score = item.get("score", 0)
                    price = item.get("sell_price", 0)
                    note = item.get("note", "")
                    message += f"{i}. <b>{name}</b>\n"
                    message += f"    ${price} | 🤖 {score}/10\n"
                    if note:
                        message += f"   📝 {note}\n\n"

            message += f"\n💡 لحذف منتج: <code>/wishlist remove {wishlist_id} اسم المنتج</code>"

            await update.message.reply_text(message, parse_mode="HTML")

        elif action == "delete":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "️ يرجى كتابة رقم القائمة.\n"
                    "مثال: <code>/wishlist delete 1</code>",
                    parse_mode="HTML"
                )
                return

            try:
                wishlist_id = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ رقم القائمة يجب أن يكون رقماً.")
                return

            from backend.wishlists import delete_wishlist
            success = delete_wishlist(user_id, wishlist_id)

            if success:
                await update.message.reply_text(f"✅ تم حذف القائمة رقم {wishlist_id}.")
            else:
                await update.message.reply_text("❌ القائمة غير موجودة أو لا تملكينها.")

        elif action == "remove":
            if len(context.args) < 3:
                await update.message.reply_text(
                    "⚠️ طريقة الاستخدام:\n"
                    "<code>/wishlist remove رقم_القائمة اسم المنتج</code>\n\n"
                    "مثال: <code>/wishlist remove 1 خلاط محمول</code>",
                    parse_mode="HTML"
                )
                return

            try:
                wishlist_id = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ رقم القائمة يجب أن يكون رقماً.")
                return

            product_name = " ".join(context.args[2:]).strip()
            from backend.wishlists import remove_from_wishlist
            success = remove_from_wishlist(user_id, wishlist_id, product_name)

            if success:
                await update.message.reply_text(
                    f"✅ تم حذف '<b>{product_name}</b>' من القائمة رقم {wishlist_id}.",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text("❌ فشل حذف المنتج من القائمة.")

        else:
            await update.message.reply_text(
                "⚠️ إجراء غير معروف. الإجراءات المتاحة:\n"
                "• <code>/wishlist</code> - عرض جميع القوائم\n"
                "• <code>/wishlist new اسم القائمة</code> - إنشاء قائمة\n"
                "• <code>/wishlist add رقم المنتج</code> - إضافة منتج\n"
                "• <code>/wishlist view رقم</code> - عرض محتوى القائمة\n"
                "• <code>/wishlist delete رقم</code> - حذف قائمة\n"
                "• <code>/wishlist remove رقم المنتج</code> - حذف منتج من قائمة",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error in wishlist_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "⭐ <b>نظام التقييمات في حلالية</b>\n\n"
                "يمكنكِ تقييم المنتجات التي حللتها سابقاً:\n\n"
                "📝 <b>إضافة تقييم:</b>\n"
                "<code>/review اسم_المنتج التقييم [تعليق]</code>\n\n"
                "مثال: <code>/review خلاط محمول 5 منتج ممتاز جداً</code>\n\n"
                "📋 <b>عرض تقييمات منتج:</b>\n"
                "<code>/reviews اسم_المنتج</code>\n\n"
                "🗑️ <b>حذف تقييمكِ:</b>\n"
                "<code>/unreview اسم_المنتج</code>\n\n"
                "📊 <b>تقييماتكِ:</b>\n"
                "<code>/myreviews</code>",
                parse_mode="HTML"
            )
            return

        action = context.args[0].lower()

        if action == "myreviews":
            from backend.reviews import get_user_reviews
            reviews = get_user_reviews(user_id)

            if not reviews:
                await update.message.reply_text(
                    "📭 لم تقومي بتقييم أي منتج بعد.\n\n"
                    "استخدمي: <code>/review اسم_المنتج التقييم [تعليق]</code>",
                    parse_mode="HTML"
                )
                return

            message = "⭐ <b>تقييماتكِ:</b>\n\n"
            for i, r in enumerate(reviews[:10], 1):
                name = r.get("product_name", "غير محدد")
                rating = r.get("rating", 0)
                comment = r.get("comment", "")
                stars = "⭐" * rating
                message += f"{i}. <b>{name}</b> {stars} ({rating}/5)\n"
                if comment:
                    message += f"   💬 {comment}\n"
                message += "\n"

            await update.message.reply_text(message, parse_mode="HTML")

        elif action == "unreview":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "⚠️ يرجى كتابة اسم المنتج.\n"
                    "مثال: <code>/unreview خلاط محمول</code>",
                    parse_mode="HTML"
                )
                return

            product_name = " ".join(context.args[1:]).strip()
            from backend.reviews import delete_review
            success = delete_review(user_id, product_name)

            if success:
                await update.message.reply_text(
                    f"✅ تم حذف تقييمكِ لـ '<b>{product_name}</b>'."
                )
            else:
                await update.message.reply_text(
                    f"❌ لم يتم العثور على تقييم لـ '<b>{product_name}</b>'."
                )

        elif action == "reviews":
            if len(context.args) < 2:
                await update.message.reply_text(
                    "⚠️ يرجى كتابة اسم المنتج.\n"
                    "مثال: <code>/reviews خلاط محمول</code>",
                    parse_mode="HTML"
                )
                return

            product_name = " ".join(context.args[1:]).strip()
            from backend.reviews import get_product_reviews
            result = get_product_reviews(product_name)

            if not result:
                await update.message.reply_text(
                    f"❌ لم يتم العثور على تقييمات لـ '<b>{product_name}</b>'.\n"
                    f"كوني أول من يقيّمه!",
                    parse_mode="HTML"
                )
                return

            total = result["total_reviews"]
            avg = result["average_rating"]
            counts = result["rating_counts"]

            stars_bar = ""
            for i in range(5, 0, -1):
                count = counts.get(i, 0)
                bar = "█" * count if count > 0 else "░"
                stars_bar += f"{i}⭐ {bar} ({count})\n"

            message = (
                f"⭐ <b>تقييمات: {result['product_name']}</b>\n\n"
                f"📊 <b>متوسط التقييم:</b> {avg}/5\n"
                f"👥 <b>عدد المقيّمين:</b> {total}\n\n"
                f"<b>توزيع التقييمات:</b>\n{stars_bar}\n"
            )

            recent_reviews = result["reviews"][:3]
            if recent_reviews:
                message += " <b>آخر التعليقات:</b>\n\n"
                for r in recent_reviews:
                    username = r.get("username") or r.get("first_name") or "مستخدم"
                    rating = r.get("rating", 0)
                    comment = r.get("comment", "")
                    stars = "⭐" * rating
                    message += f"• <b>{username}</b> {stars}\n"
                    if comment:
                        message += f"  💬 {comment}\n"
                    message += "\n"

            message += f"💡 <b>أضيفي تقييمكِ:</b>\n<code>/review {product_name} [1-5] [تعليق]</code>"

            await update.message.reply_text(message, parse_mode="HTML")

        else:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "⚠️ طريقة الاستخدام:\n"
                    "<code>/review اسم_المنتج التقييم [تعليق]</code>\n\n"
                    "مثال: <code>/review خلاط محمول 5 منتج ممتاز</code>\n\n"
                    "التقييم يجب أن يكون رقماً من 1 إلى 5.",
                    parse_mode="HTML"
                )
                return

            rating = None
            rating_index = None
            for i, arg in enumerate(context.args):
                try:
                    val = int(arg)
                    if 1 <= val <= 5:
                        rating = val
                        rating_index = i
                        break
                except ValueError:
                    continue

            if rating is None:
                await update.message.reply_text(
                    "⚠️ يجب إدخال تقييم رقمي من 1 إلى 5.\n\n"
                    "مثال: <code>/review خلاط محمول 5 منتج ممتاز</code>",
                    parse_mode="HTML"
                )
                return

            product_name = " ".join(context.args[1:rating_index]).strip()
            if not product_name:
                await update.message.reply_text(
                    "⚠️ يرجى كتابة اسم المنتج قبل التقييم.\n"
                    "مثال: <code>/review خلاط محمول 5 منتج ممتاز</code>",
                    parse_mode="HTML"
                )
                return

            comment = " ".join(context.args[rating_index + 1:]).strip() if rating_index < len(context.args) - 1 else None

            from backend.reviews import add_review
            success, status, data = add_review(user_id, product_name, rating, comment)

            if not success:
                await update.message.reply_text(f"❌ {data}")
                return

            from backend.points import add_points
            add_points(user_id, "review", f"تقييم {product_name} بـ {rating} نجوم")

            stars = "⭐" * rating
            if status == "updated":
                message = (
                    f"✅ تم تحديث تقييمكِ لـ '<b>{product_name}</b>'\n\n"
                    f"التقييم الجديد: {stars} ({rating}/5)"
                )
            else:
                message = (
                    f"✅ شكراً لتقييمكِ '<b>{product_name}</b>'!\n\n"
                    f"تقييمكِ: {stars} ({rating}/5)"
                )

            if comment:
                message += f"\n💬 تعليقكِ: {comment}"

            await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in review_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        from backend.points import get_user_profile

        profile = get_user_profile(user_id)

        if not profile:
            await update.message.reply_text("❌ لم يتم العثور على ملفك الشخصي.")
            return

        total = profile.get('total_points', 0)
        next_pts = profile.get('points_to_next', 0)
        progress_pct = min(100, int((total / (total + next_pts)) * 100)) if (total + next_pts) > 0 else 0
        progress_bar = "█" * (progress_pct // 10) + "░" * (10 - progress_pct // 10)

        message = (
            f" <b>ملفكِ الشخصي في حلالية</b>\n\n"
            f" <b>الشارة:</b> {profile['current_badge']}\n"
            f" <b>المستوى:</b> {profile['level']}\n"
            f"⭐ <b>النقاط:</b> {total}\n\n"
            f"📈 <b>التقدم للشارة التالية:</b>\n"
            f"<code>{progress_bar}</code> {progress_pct}%\n"
            f"المتبقي: <b>{next_pts}</b> نقطة لـ <b>{profile['next_badge']}</b>\n\n"
            f"📋 <b>إحصائياتكِ:</b>\n"
            f"🔍 عمليات البحث: {profile.get('searches_count', 0)}\n"
            f"⭐ التقييمات: {profile.get('reviews_count', 0)}\n"
            f"💾 المفضلة: {profile.get('saves_count', 0)}\n"
        )

        recent = profile.get('recent_activity', [])
        if recent:
            message += "\n <b>آخر الأنشطة:</b>\n"
            action_names = {"search": " تحليل", "save": "💾 حفظ", "review": "⭐ تقييم", "alert": " تنبيه", "wishlist_create": " قائمة جديدة"}
            for act in recent[:3]:
                name = action_names.get(act['action'], act['action'])
                message += f"• {name} (+{act['points']} نقطة)\n"

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in profile_command: {e}", exc_info=True)
        await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")


async def halal_guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🕌 <b>منهجية حلالية في ضمان النقاء والثقة</b>\n\n"
        "نحن في حلالية نؤمن بأن التسوق الآمن حق لكل امرأة. لذلك، قمنا ببناء محرك فحص ذكي يعتمد على:\n\n"
        "🟢 <b>حلال (موثوق):</b>\n"
        "لا يحتوي على أي مكونات محرمة أو مشتقات حيوانية مشبوهة.\n\n"
        "🟡 <b>يحتاج تحقق (مختلف عليه):</b>\n"
        "قد يحتوي على مكونات مثل (الجيلاتين، الغليسيرين الحيواني، الكارمين). ننصحك بمراجعة الشركة المصنعة للتأكد من مصدرها.\n\n"
        "🔴 <b>غير حلال (مرفوض):</b>\n"
        "يحتوي بشكل قاطع على (كحول إيثيلي، دهون خنزير، مشتقاته، أو إنزيمات حيوانية محرمة).\n\n"
        "⚖️ <b>مصادرنا:</b>\n"
        "نعتمد في تصنيفنا على قوائم مكونات معتمدة من هيئات رقابية عالمية، ونقوم بالتحديث المستمر.\n\n"
        "💡 <b>نصيحة:</b> إذا شككتِ في أي منتج، استخدمي أمر /report لإبلاغنا وسنراجعه فوراً."
    )
    await update.message.reply_text(message, parse_mode="HTML")


async def daily_pick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from backend.database import get_top_products
        products = get_top_products(limit=5)

        if not products:
            await update.message.reply_text("📭 لا توجد منتجات مقترحة حالياً.")
            return

        import random
        pick = random.choice([dict(p) for p in products])

        message = (
            f" <b>اختيار حلالية لكِ اليوم!</b>\n\n"
            f"️ <b>{pick['product_name']}</b>\n"
            f"⭐ التقييم: {pick.get('rating', 4.5)}/5\n"
            f"🤖 درجة الثقة: {pick.get('score', 8)}/10\n"
            f"💰 السعر التقريبي: ${pick.get('sell_price', 0)}\n\n"
            f"💡 {pick.get('recommendation', 'منتج ممتاز')}\n\n"
            f"اكتبي اسم هذا المنتج في المحادثة لتحليله وتفصيل مكوناته! 👇"
        )
        await update.message.reply_text(message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in daily_pick_command: {e}")
        await update.message.reply_text("❌ حدث خطأ في جلب الاقتراح.")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """أمر /usage - عرض إحصائيات الاستخدام"""
            try:
                user_id = str(update.effective_user.id)

                from backend.rate_limiter import rate_limiter

                # الحصول على إحصائيات كل إجراء
                actions = ['analyze', 'search', 'save', 'review', 'alert', 'wishlist']

                message = "📊 <b>إحصائيات استخدامك:</b>\n\n"

                for action in actions:
                    stats = rate_limiter.get_usage_stats(user_id, action)
                    limit_config = rate_limiter.limits.get(action, rate_limiter.limits['default'])

                    message += f"<b>{limit_config['name']}:</b>\n"
                    message += f"   المستخدم: {stats['used']}/{stats['limit']}\n"
                    message += f"   المتبقي: {stats['remaining']}\n"
                    message += f"   النسبة: {stats['percentage_used']:.1f}%\n\n"

                message += "💡 <b>نصيحة:</b> الحدود تُعاد تعيينها كل ساعة."

                await update.message.reply_text(message, parse_mode="HTML")

            except Exception as e:
                logger.error(f"Error in usage_command: {e}", exc_info=True)
                await update.message.reply_text("❌ عذراً، حدث خطأ غير متوقع.")