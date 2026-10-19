import requests

from telegram_bot.config import API_URL, TIMEOUT


# ==========================================
# ANALYZE PRODUCT
# ==========================================

def analyze_product(
    product_name,
    reviews=0,
    rating=0,
    price=0
):

    try:

        response = requests.post(

            API_URL,

            json={

                "product_name": product_name,

                "reviews": reviews,

                "rating": rating,

                "price": price

            },

            timeout=TIMEOUT

        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "error": "SERVER_OFF"
        }

    except requests.exceptions.Timeout:

        return {
            "error": "TIMEOUT"
        }

    except requests.exceptions.HTTPError as e:

        return {
            "error": f"HTTP_{response.status_code}"
        }

    except Exception as e:

        return {
            "error": str(e)
        }


# ==========================================
# SAVED PRODUCTS
# ==========================================

def get_saved_products():

    try:

        response = requests.get(

            "http://127.0.0.1:8000/saved",

            timeout=TIMEOUT

        )

        response.raise_for_status()

        return response.json()

    except Exception:

        return []


# ==========================================
# DISCOVERY ENGINE
# ==========================================

def get_hunt_products():

    try:

        response = requests.get(

            "http://127.0.0.1:8000/hunt",

            timeout=TIMEOUT

        )

        response.raise_for_status()

        return response.json()

    except Exception:

        return []


# ==========================================
# SERVER CHECK
# ==========================================

def server_status():

    try:

        response = requests.get(

            "http://127.0.0.1:8000/",

            timeout=5

        )

        return response.status_code == 200

    except Exception:

        return False