from fastapi import FastAPI

from app.api import orders

app = FastAPI(title="checkout")
app.include_router(orders.router)
