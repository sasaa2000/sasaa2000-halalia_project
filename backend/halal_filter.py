"""
حلالية - فلتر المكونات المحرمة
نظام فحص ذكي يحدد حالة الحلال لكل منتج
"""

import logging
from backend.db import db

logger = logging.getLogger(__name__)

# قائمة المكونات المحرمة (للفحص السريع بدون قاعدة بيانات)
HARAM_LIST = {
    # الكحول
    'alcohol', 'ethanol', 'ethyl alcohol', 'denatured alcohol',
    'benzyl alcohol', 'isopropyl alcohol', 'methanol', 'butyl alcohol',
    'كحول', 'إيثانول', 'كحول إيثيلي', 'كحول محول', 'كحول بنزيلي',
    
    # الخنزير
    'pork', 'lard', 'swine', 'porcine', 'pig', 'boar',
    'pork fat', 'swine fat', 'porcine gelatin', 'porcine enzymes',
    'دهن الخنزير', 'لارد', 'شحم الخنزير', 'جيلاتين الخنزير',
    
    # الكارمين
    'carmine', 'cochineal', 'e120', 'carminic acid',
    'كارمين', 'كوشينيل',
    
    # مواد ضارة
    'paraben', 'methylparaben', 'propylparaben', 'phthalates',
    'triclosan', 'toluene', 'formaldehyde',
    'بارابين', 'فثالات', 'تريكلوسان', 'تولوين', 'فورمالديهايد'
}

# قائمة المكونات المشبوهة (تحتاج تحقق)
DOUBTFUL_LIST = {
    'gelatin', 'animal gelatin', 'animal rennet', 'pepsin',
    'animal enzymes', 'animal lipase', 'lanolin', 'elastin',
    'animal collagen', 'animal sterol', 'cholesterol', 'squalene',
    'animal glycerin', 'glycerol', 'animal hyaluronic acid',
    'جيلاتين', 'جيلاتين حيواني', 'المنفحة الحيوانية', 'بيبسين',
    'إنزيمات حيوانية', 'ليباز حيواني', 'لانولين', 'إيلاستين',
    'كولاجين حيواني', 'ستيرول حيواني', 'كوليسترول', 'سكوالين',
    'غليسيرين حيواني', 'غليسيرول', 'حمض الهيالورونيك الحيواني',
    'جيلاتين',  # ✅ أضف هذا السطر (بـ "ة")
}

def check_ingredients(product_name, ingredients_text=None):
    """
    فحص مكونات المنتج وتحديد حالة الحلال

    Args:
        product_name: اسم المنتج
        ingredients_text: قائمة المكونات (نص أو قائمة)

    Returns:
        dict: {
            'status': 'halal' | 'doubtful' | 'haram',
            'haram_items': [],
            'doubtful_items': [],
            'confidence': float,
            'message': str
        }
    """
    result = {
        'status': 'halal',
        'haram_items': [],
        'doubtful_items': [],
        'confidence': 100,
        'message': 'لا توجد مكونات محرمة ظاهرة',
        'checked_from_db': False
    }

    # 1. فحص اسم المنتج نفسه
    name_lower = product_name.lower()

    # ✅ فحص المحرمات في اسم المنتج
    for haram in HARAM_LIST:
        if haram in name_lower:
            result['status'] = 'haram'
            result['haram_items'].append(haram)
            result['confidence'] = 0
            result['message'] = f'المنتج يحتوي على مكون محرم: {haram}'
            return result

    # ✅ فحص المشبوهات في اسم المنتج (هذا كان ناقصاً!)
    for doubtful in DOUBTFUL_LIST:
        if doubtful in name_lower:
            result['status'] = 'doubtful'
            if doubtful not in result['doubtful_items']:
                result['doubtful_items'].append(doubtful)
            result['confidence'] = min(result['confidence'], 50)

    # 2. فحص قائمة المكونات (إن وجدت)
    if ingredients_text:
        ingredients_lower = ingredients_text.lower() if isinstance(ingredients_text, str) else ' '.join(
            ingredients_text).lower()

        # فحص المحرمات
        for haram in HARAM_LIST:
            if haram in ingredients_lower:
                result['status'] = 'haram'
                if haram not in result['haram_items']:
                    result['haram_items'].append(haram)
                result['confidence'] = 0

        # فحص المشبوهات
        for doubtful in DOUBTFUL_LIST:
            if doubtful in ingredients_lower:
                if result['status'] != 'haram':
                    result['status'] = 'doubtful'
                if doubtful not in result['doubtful_items']:
                    result['doubtful_items'].append(doubtful)
                result['confidence'] = min(result['confidence'], 50)

    # 3. الفحص من قاعدة البيانات (إذا لم نجد شيئاً)
    if result['status'] == 'halal' and not result['haram_items']:
        try:
            db_result = db.execute_query(
                """SELECT name_en, name_ar, category, severity 
                   FROM haram_ingredients 
                   WHERE LOWER(name_en) LIKE %s OR LOWER(name_ar) LIKE %s""",
                (f'%{name_lower}%', f'%{name_lower}%'),
                fetch=True
            )

            if db_result:
                result['checked_from_db'] = True
                for row in db_result:
                    severity = row.get('severity', 'haram')
                    name = row.get('name_ar') or row.get('name_en')

                    if severity == 'haram':
                        result['status'] = 'haram'
                        result['haram_items'].append(name)
                        result['confidence'] = 0
                    elif severity == 'doubtful':
                        if result['status'] != 'haram':
                            result['status'] = 'doubtful'
                        result['doubtful_items'].append(name)
                        result['confidence'] = min(result['confidence'], 50)
                    elif severity == 'makruh':
                        result['doubtful_items'].append(f"{name} (مكروه)")
                        result['confidence'] = min(result['confidence'], 70)
        except Exception as e:
            logger.error(f"خطأ في فحص قاعدة البيانات: {e}")

    # 4. تحديد الرسالة النهائية
    if result['status'] == 'haram':
        items = ', '.join(result['haram_items'][:3])
        result['message'] = f'❌ يحتوي على مكونات محرمة: {items}'
    elif result['status'] == 'doubtful':
        items = ', '.join(result['doubtful_items'][:3])
        result['message'] = f'⚠️ يحتوي على مكونات مشبوهة: {items}'
    else:
        result['message'] = '✅ لا توجد مكونات محرمة ظاهرة'

    return result

def get_halal_status_emoji(status):
    """إرجاع الإيموجي المناسب لحالة الحلال"""
    emojis = {
        'halal': '✅',
        'doubtful': '⚠️',
        'haram': '❌',
        'unknown': '❓'
    }
    return emojis.get(status, '❓')


def get_halal_status_arabic(status):
    """إرجاع النص العربي لحالة الحلال"""
    texts = {
        'halal': 'حلال',
        'doubtful': 'يحتاج تحقق',
        'haram': 'غير حلال',
        'unknown': 'غير محدد'
    }
    return texts.get(status, 'غير محدد')


def format_halal_report(check_result):
    """تنسيق تقرير الحلال للعرض"""
    status = check_result['status']
    emoji = get_halal_status_emoji(status)
    status_ar = get_halal_status_arabic(status)
    
    report = f"{emoji} <b>حالة الحلال:</b> {status_ar}\n"
    
    if check_result['haram_items']:
        report += f"❌ <b>مكونات محرمة:</b> {', '.join(check_result['haram_items'][:5])}\n"
    
    if check_result['doubtful_items']:
        report += f"⚠️ <b>مكونات مشبوهة:</b> {', '.join(check_result['doubtful_items'][:5])}\n"
    
    report += f"📊 <b>درجة الثقة:</b> {check_result['confidence']}%\n"
    
    return report