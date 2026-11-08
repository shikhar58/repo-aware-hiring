from acme_payments import charge, idempotency_key
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/orders")


class OrderIn(BaseModel):
    customer_id: str
    amount_cents: int


@router.post("")
def place_order(order: OrderIn):
    key = idempotency_key(order.customer_id, order.amount_cents)
    try:
        result = charge(order.customer_id, order.amount_cents)
    except Exception as exc:  # provider down: surface as 502
        raise HTTPException(502, "payment failed") from exc
    return {"charge": result.id, "key": key, "status": result.status}
