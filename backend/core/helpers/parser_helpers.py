import re
from decimal import Decimal
from urllib.parse import urljoin

# ==========================================================
# Clean Text
# ==========================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# ==========================================================
# Normalize URL
# ==========================================================

def normalize_url(url, base=""):

    if not url:
        return ""

    url = url.strip()

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        return urljoin(base, url)

    return url

# ==========================================================
# Safe Float
# ==========================================================

def safe_float(value):

    if value is None:
        return None

    try:

        value = str(value)

        value = value.replace(",", "")
        value = value.replace("$", "")
        value = value.replace("£", "")
        value = value.replace("€", "")
        value = value.strip()

        return float(value)

    except Exception:

        return None

# ==========================================================
# Safe Integer
# ==========================================================

def safe_int(value):

    if value is None:
        return 0

    try:

        value = re.sub(r"[^\d]", "", str(value))

        if value == "":
            return 0

        return int(value)

    except Exception:

        return 0

# ==========================================================
# Extract Rating
# ==========================================================

def extract_rating(text):

    if not text:
        return 0.0

    match = re.search(r"([\d.]+)", text)

    if not match:
        return 0.0

    return safe_float(match.group(1)) or 0.0

# ==========================================================
# Extract Reviews
# ==========================================================

def extract_reviews(text):

    return safe_int(text)

# ==========================================================
# Extract Price
# ==========================================================

def extract_price(whole, fraction="00"):

    if whole is None:
        return None

    whole = re.sub(r"[^\d]", "", str(whole))

    fraction = re.sub(r"[^\d]", "", str(fraction))

    if fraction == "":
        fraction = "00"

    try:

        value = Decimal(f"{whole}.{fraction}")

        return float(value)

    except Exception:

        return None

# ==========================================================
# Normalize Image
# ==========================================================

def normalize_image(url):

    return normalize_url(url)

# ==========================================================
# Remove Duplicate Spaces
# ==========================================================

def normalize_spaces(text):

    return clean_text(text)