import json
import os

from pytrends.request import TrendReq

CACHE_FILE = "backend/google_cache.json"


def load_cache():

    if not os.path.exists(CACHE_FILE):
        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:
        return {}


def save_cache(cache):

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            cache,
            f,
            ensure_ascii=False,
            indent=4
        )


def get_google_trend_data(keyword):

    try:

        cache = load_cache()

        key = keyword.lower()

        if key in cache:
            return cache[key]

        pytrend = TrendReq()

        pytrend.build_payload(
            [keyword],
            timeframe="today 3-m"
        )

        data = pytrend.interest_over_time()

        if data.empty:

            result = {
                "google_trend": 0,
                "trend_direction": "غير معروف"
            }

            cache[key] = result
            save_cache(cache)

            return result

        trend_score = int(
            data[keyword].mean()
        )

        first_value = int(
            data[keyword].iloc[0]
        )

        last_value = int(
            data[keyword].iloc[-1]
        )

        if last_value > first_value:
            direction = "📈 صاعد"

        elif last_value < first_value:
            direction = "📉 هابط"

        else:
            direction = "➡️ ثابت"

        result = {
            "google_trend": trend_score,
            "trend_direction": direction
        }

        cache[key] = result

        save_cache(cache)

        return result

    except Exception as e:

        print(
            "GOOGLE TREND ERROR =",
            e
        )

        return {
            "google_trend": 0,
            "trend_direction": "غير معروف"
        }


def get_google_trend_score(keyword):

    data = get_google_trend_data(
        keyword
    )

    return data["google_trend"]