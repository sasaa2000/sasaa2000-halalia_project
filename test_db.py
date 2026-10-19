"""
اختبار الاتصال بقاعدة بيانات حلالية
"""

from backend.db import db

print(" اختبار الاتصال بقاعدة بيانات حلالية...\n")

try:
    # اختبار الاتصال
    conn = db.get_connection()
    print("✅ تم الاتصال بقاعدة البيانات بنجاح")
    
    # اختبار إنشاء مستخدم تجريبي
    user = db.execute_one(
        "INSERT INTO users (telegram_id, username, first_name) VALUES (%s, %s, %s) RETURNING id",
        (999999, 'test_user', 'Test')
    )
    print(f"✅ تم إنشاء مستخدم تجريبي: ID = {user['id']}")
    
    # اختبار جلب المستخدمين
    users = db.execute_query("SELECT * FROM users", fetch=True)
    print(f"✅ عدد المستخدمين في القاعدة: {len(users)}")
    
    # تنظيف البيانات التجريبية
    db.execute_query("DELETE FROM users WHERE telegram_id = 999999")
    print("✅ تم حذف البيانات التجريبية")
    
    print("\n🎉 جميع الاختبارات نجحت! قاعدة البيانات جاهزة.")
    
except Exception as e:
    print(f"❌ فشل الاختبار: {e}")
finally:
    db.close()