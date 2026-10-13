import random


USER_AGENTS = [

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/135.0 Safari/537.36",

]


class HeaderManager:

    @staticmethod
    def build():

        return {

            "User-Agent": random.choice(USER_AGENTS),

            "Accept-Language": "en-US,en;q=0.9",

            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "image/avif,"
                "image/webp,*/*;q=0.8"
            ),

            "Connection": "keep-alive",

            "Cache-Control": "no-cache",

        }