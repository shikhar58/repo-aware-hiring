"""Orders API (synthetic fixture for repo-aware-hiring tests)."""
import sentry_sdk
from fastapi import Depends, FastAPI

from app.auth import current_user
from app.db import list_orders

sentry_sdk.init()
app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/orders")
def orders(user=Depends(current_user)):
    return list_orders(user["id"])
