![Tests](https://github.com/sasaa2000/halalia_project/actions/workflows/tests.yml/badge.svg)

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Halalia Engine", version="0.1")


# --------- Models ---------
class ProductRequest(BaseModel):
    product: str
    country: str = "EG"
    platform: str = "Shopify"
    goal: str = "profit"


class ProductResponse(BaseModel):
    score: float
    demand: str
    competition: str
    profit: str
    recommendation: str


# --------- Logic ---------
def analyze_logic(product: str) -> ProductResponse:
    name = product.lower()

    if "mask" in name or "led" in name:
        return ProductResponse(
            score=8.2,
            demand="مرتفع",
            competition="متوسطة",
            profit="جيدة",
            recommendation="منتج قوي للتجربة بإعلان صغير"
        )

    if "charger" in name or "power" in name:
        return ProductResponse(
            score=7.5,
            demand="مرتفع",
            competition="عالية",
            profit="متوسطة",
            recommendation="يحتاج ميزة تنافسية واضحة"
        )

    return ProductResponse(
        score=6.0,
        demand="متوسط",
        competition="عالية",
        profit="ضعيفة",
        recommendation="غير مناسب كبداية"
    )


# --------- Routes ---------
@app.get("/")
def home():
    return {"status": "Halalia Engine is running"}


@app.post("/analyze", response_model=ProductResponse)
def analyze_product(request: ProductRequest):
    return analyze_logic(request.product)


pytest>=8.0
pytest-cov>=5.0
pytest-mock>=3.12
pytest-asyncio>=0.23
anyio>=4.0



