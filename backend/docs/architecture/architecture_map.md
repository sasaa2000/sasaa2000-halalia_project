# HALALIA Architecture Map (Verified Reality)

هذا الملف يوثق البنية المعمارية **الفعلية والمُختبرة** للمشروع، وليس الطموحات المستقبلية.

## 1. طبقة الواجهة (Interface Layer)
- **Telegram Bot (`telegram_bot/`)**: نقطة الدخول للمستخدم.
  - `bot.py`: نقطة التشغيل الرئيسية.
  - `api_client.py`: العميل الذي يتصل بـ Backend عبر HTTP.
  - `handlers.py`: معالجة الأوامر (`/start`, `/top`, `/hunt`, ومقارنة `vs`).

## 2. طبقة API (Gateway Layer)
- **FastAPI Server (`backend/main.py`)**:
  - `GET /`: فحص صحة السيرفر.
  - `GET /hunt`: جلب أفضل المنتجات.
  - `GET /saved`: جلب المنتجات المحفوظة.
  - `POST /analyze`: نقطة الدخول الرئيسية لتحليل المنتجات.

## 3. طبقة المعالجة (Pipeline & Engines)
- **Hunter Pipeline (`backend/hunter_pipeline.py`)**: المنسق الرئيسي الذي يربط المحركات ببعضها.
- **محركات التحليل (Engines)**:
  - `advanced_ai.py`: حساب الدرجة الأساسية والكلمات المفتاحية.
  - `trend_engine.py`: تحليل اتجاهات السوق و Google Trends.
  - `competition_engine.py`: حساب مستوى المنافسة.
  - `market_intelligence.py`: تحليل تشبع السوق والربحية.
  - `ranking/__init__.py` (`rank_product`): دالة الجسر التي تحول الأرقام إلى تصنيف (A/B/C/D).

## 4. طبقة البيانات (Data Layer)
- **Local Storage (`backend/database.py`)**: حفظ واسترجاع المنتجات المحللة في `products_db.json`.

## 5. الطبقة الأساسية (Core Foundation) - مُختبرة
- **Configuration**: إدارة الإعدادات.
- **Logging**: نظام تسجيل الأحداث (تغطية اختبارات > 88%).
- **Monitoring**: نظام المقاييس (Metrics).

---
**ملاحظة هامة:** أي مجلدات أخرى في المشروع (مثل `platform/`, `security/`, `observability/`) تحتوي على ملفات بحجم 0 bytes هي هياكل مؤجلة ولا تُعتبر جزءاً من سير العمل الحالي حتى يتم تنفيذها واختبارها.