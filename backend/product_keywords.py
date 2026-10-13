KEYWORD_SCORES = {

    # PET
    "pet": 2,
    "cat": 3,
    "dog": 3,
    "feeder": 2,
    "cleaner": 2,

    # SMART
    "smart": 1,
    "wifi": 2,
    "bluetooth": 2,

    # FITNESS
    "fitness": 2,
    "gym": 2,
    "workout": 2,

    # BEAUTY
    "beauty": 2,
    "makeup": 2,
    "facial": 2,

    # HOME
    "lamp": 1,
    "light": 1,
    "vacuum": 2,

    # KITCHEN
    "blender": 2,
    "coffee": 2,
    "kitchen": 1,

    # TREND WORDS
    "wireless": 1,
    "portable": 1,
    "automatic": 1,
    "mini": 1,
    "rechargeable": 1,
    "usb": 1
}


def get_keyword_bonus(product_name):

    name = product_name.lower()

    bonus = 0

    matched_keywords = []

    for keyword, value in KEYWORD_SCORES.items():

        if keyword in name:

            bonus += value

            matched_keywords.append(keyword)

    return {
        "keyword_bonus": bonus,
        "matched_keywords": matched_keywords
    }