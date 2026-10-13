CATEGORY_KEYWORDS = {

    "pet": [
        "pet",
        "cat",
        "dog",
        "feeder",
        "cleaner"
    ],

    "smart": [
        "smart",
        "wifi",
        "bluetooth",
        "lock",
        "watch"
    ],

    "gaming": [
        "gaming",
        "mouse",
        "keyboard"
    ],

    "beauty": [
        "beauty",
        "facial",
        "makeup",
        "mask",
        "mirror"
    ],

    "fitness": [
        "fitness",
        "gym",
        "workout"
    ],

    "baby": [
        "baby",
        "monitor"
    ],

    "kitchen": [
        "blender",
        "coffee",
        "kitchen"
    ]
}


CATEGORY_BONUS = {

    "pet": 3,

    "smart": 2,

    "gaming": 2,

    "beauty": 2,

    "fitness": 2,

    "baby": 1,

    "kitchen": 1,

    "general": 0
}


def get_category_bonus(category):

    return CATEGORY_BONUS.get(
        category,
        0
    )