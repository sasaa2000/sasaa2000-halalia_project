from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Product:

    # ==========================================
    # Identity
    # ==========================================

    asin: Optional[str] = None
    sku: Optional[str] = None

    # ==========================================
    # Basic Information
    # ==========================================

    product_name: str = ""
    description: str = ""

    # ==========================================
    # Pricing
    # ==========================================

    price: Optional[float] = None
    original_price: Optional[float] = None
    discount: Optional[float] = None

    currency: str = "USD"

    # ==========================================
    # Rating
    # ==========================================

    rating: float = 0.0
    reviews: int = 0

    # ==========================================
    # Images
    # ==========================================

    image: str = ""
    thumbnail: str = ""

    # ==========================================
    # Links
    # ==========================================

    url: str = ""

    # ==========================================
    # Provider
    # ==========================================

    source: str = ""

    # ==========================================
    # Amazon Flags
    # ==========================================

    is_prime: bool = False
    is_sponsored: bool = False
    amazon_choice: bool = False
    best_seller: bool = False

    # ==========================================
    # Availability
    # ==========================================

    in_stock: bool = True

    # ==========================================
    # Ranking
    # ==========================================

    score: float = 0.0

    # ==========================================
    # Metadata
    # ==========================================

    metadata: Dict[str, Any] = field(default_factory=dict)

    # ==========================================
    # Convert To Dictionary
    # ==========================================

    def to_dict(self):

        return {

            "asin": self.asin,

            "sku": self.sku,

            "product_name": self.product_name,

            "description": self.description,

            "price": self.price,

            "original_price": self.original_price,

            "discount": self.discount,

            "currency": self.currency,

            "rating": self.rating,

            "reviews": self.reviews,

            "image": self.image,

            "thumbnail": self.thumbnail,

            "url": self.url,

            "source": self.source,

            "is_prime": self.is_prime,

            "is_sponsored": self.is_sponsored,

            "amazon_choice": self.amazon_choice,

            "best_seller": self.best_seller,

            "in_stock": self.in_stock,

            "score": self.score,

            "metadata": self.metadata

        }