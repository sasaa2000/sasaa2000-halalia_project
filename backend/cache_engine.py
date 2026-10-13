import time

CACHE = {}

CACHE_TIME = 60 * 60  # ساعة واحدة


def get_cache(key):

    if key not in CACHE:
        return None

    item = CACHE[key]

    if time.time() - item["time"] > CACHE_TIME:

        del CACHE[key]

        return None

    return item["data"]


def save_cache(key, data):

    CACHE[key] = {

        "time": time.time(),

        "data": data

    }


def clear_cache():

    CACHE.clear()