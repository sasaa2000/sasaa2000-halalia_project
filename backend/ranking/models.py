from dataclasses import dataclass


@dataclass
class ProductScore:

    final_score: float = 0.0

    price_score: float = 0.0

    rating_score: float = 0.0

    review_score: float = 0.0

    prime_score: float = 0.0

    bestseller_score: float = 0.0

    choice_score: float = 0.0

    sponsored_penalty: float = 0.0