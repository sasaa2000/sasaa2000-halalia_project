from pydantic import BaseModel

class ProductRequest(BaseModel):
    product_name: str

class ProductResponse(BaseModel):
    product_name: str
    score: float
    demand: str
    competition: str
    profitability: str
    recommendation: str
    