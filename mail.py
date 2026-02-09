from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Demo REST API")

class Item(BaseModel):
    name: str
    price: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id, "name": "exemple", "price": 9.99}

@app.post("/items")
def create_item(item: Item):
    return {"created": True, "item": item}
