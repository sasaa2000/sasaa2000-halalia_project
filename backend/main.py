from fastapi import FastAPI

from backend.hunter_pipeline import run_custom_pipeline

from backend.discovery_engine import get_top_products

from backend.database import load_products
from backend.database import save_product

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "AI Product Hunter Running 🚀"
    }

@app.get("/hunt")
def hunt_products():

    return get_top_products()

@app.get("/saved")
def get_saved_products():

    products = load_products()

    products.sort(
        key=lambda x: x.get("score", 0),
        reverse=True
    )

    return products[:10]

@app.post("/analyze")
def analyze_product(data: dict):

    product_name = data.get("product_name", "").strip()

    if not product_name:
        return {
            "error": "اسم المنتج فارغ"
        }

    result = orchestrator.analyze_product(
        product_name
    )

    save_product(result)

    return result