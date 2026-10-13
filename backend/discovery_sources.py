"""
AI Product Hunter
Discovery Sources

هذا الملف يحتوى على جميع مصادر البحث التى
سيستخدمها البوت لاكتشاف المنتجات.

حالياً هى مجرد إعدادات (Configuration).

لاحقاً سيتم ربط كل مصدر بمحرك البحث الخاص به.
"""

DISCOVERY_SOURCES = {

    "amazon": {
        "enabled": True,
        "priority": 1,
        "country": "US"
    },

    "aliexpress": {
        "enabled": True,
        "priority": 2
    },

    "cjdropshipping": {
        "enabled": True,
        "priority": 3
    },

    "google_trends": {
        "enabled": True,
        "priority": 4
    },

    "tiktok": {
        "enabled": True,
        "priority": 5
    },

    "temu": {
        "enabled": False,
        "priority": 6
    }

}


def get_enabled_sources():
    """
    ترجع أسماء المصادر المفعلة فقط.
    """

    sources = []

    for name, data in DISCOVERY_SOURCES.items():

        if data.get("enabled", False):

            sources.append(name)

    return sources


def is_source_enabled(source_name):
    """
    التحقق من أن المصدر مفعل.
    """

    source = DISCOVERY_SOURCES.get(source_name)

    if not source:
        return False

    return source.get("enabled", False)


def get_source_priority(source_name):
    """
    ترجع أولوية المصدر.
    """

    source = DISCOVERY_SOURCES.get(source_name)

    if not source:
        return 999

    return source.get("priority", 999)


def get_sources_sorted():
    """
    ترجع المصادر مرتبة حسب الأولوية.
    """

    enabled = []

    for name, data in DISCOVERY_SOURCES.items():

        if data.get("enabled", False):

            enabled.append(
                (
                    name,
                    data["priority"]
                )
            )

    enabled.sort(
        key=lambda item: item[1]
    )

    return [item[0] for item in enabled]