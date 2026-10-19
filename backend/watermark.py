"""
حلالية - نظام العلامة المائية للصور
"""
import logging
import requests
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import io

logger = logging.getLogger(__name__)


class Watermarker:
    def __init__(self):
        self.watermark_text = "Halalia.com"
        try:
            self.font = ImageFont.truetype("arial.ttf", 30)
        except:
            self.font = ImageFont.load_default()

    def add_watermark(self, image_url: str) -> str:
        """
        تحميل صورة وإضافة علامة مائية

        Returns:
            str: رابط الصورة الأصلية (سنعدلها مباشرة في الذاكرة)
        """
        try:
            # تحميل الصورة
            response = requests.get(image_url, timeout=10)
            img = Image.open(io.BytesIO(response.content))

            # تحويل إلى RGBA
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # إنشاء طبقة شفافة
            txt = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt)

            # رسم العلامة المائية (أسفل يمين)
            w, h = img.size
            draw.text((w - 150, h - 40), self.watermark_text,
                      font=self.font, fill=(255, 255, 255, 200))

            # دمج الطبقات
            watermarked = Image.alpha_composite(img, txt)

            # حفظ في ذاكرة مؤقتة
            output = io.BytesIO()
            watermarked.convert("RGB").save(output, format="JPEG")
            output.seek(0)

            # إرجاع كائن الملف
            return output

        except Exception as e:
            logger.error(f"خطأ في العلامة المائية: {e}")
            return None


watermarker = Watermarker()