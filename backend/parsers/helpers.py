import re
from urllib.parse import urljoin


# ==========================================================
# Text
# ==========================================================

def clean_text(text):

    if not text:
        return ""

    return " ".join(
        text.replace("\n", " ").split()
    )


# ==========================================================
# Price
# ==========================================================

def extract_price(value):

    if not value:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = value.replace(",", "")

    result = re.findall(r"\d+\.\d+|\d+", value)

    if not result:
        return None

    try:
        return float(result[0])
    except Exception:
        return None


# ==========================================================
# Rating
# ==========================================================

def extract_rating(text):

    if not text:
        return 0.0

    result = re.findall(r"\d+(\.\d+)?", text)

    if not result:
        return 0.0

    try:
        number = re.search(r"\d+(\.\d+)?", text)

        if number:
            return float(number.group())

    except Exception:
        pass

    return 0.0


# ==========================================================
# Reviews
# ==========================================================

def extract_reviews(text):

    if not text:
        return 0

    text = text.replace(",", "")

    result = re.findall(r"\d+", text)

    if not result:
        return 0

    try:
        return int(result[0])
    except Exception:
        return 0


# ==========================================================
# URL
# ==========================================================

def normalize_url(url, base="https://www.amazon.com"):

    if not url:
        return ""

    return urljoin(base, url)


# ==========================================================
# Image
# ==========================================================

def normalize_image(url):

    if not url:
        return ""

    return normalize_url(url)


# ==========================================================
# Boolean
# ==========================================================

def has_text(node, keyword):

    if node is None:
        return False

    return keyword.lower() in node.get_text(" ", strip=True).lower()


# ==========================================================
# Safe Attribute
# ==========================================================

def attr(node, name, default=""):

    if node is None:
        return default

    return node.get(name, default)


# ==========================================================
# Safe Text
# ==========================================================

def text(node):

    if node is None:
        return ""

    return clean_text(node.get_text())