import os

import acme_payments
import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/invoices")
CHECKOUT_URL = os.environ.get("CHECKOUT_URL", "http://checkout:8000")


@router.post("/{invoice_id}/refund")
def refund_invoice(invoice_id: str, charge_id: str, amount_cents: int | None = None):
    order = httpx.get(f"{CHECKOUT_URL}/orders/by-charge/{charge_id}", timeout=3).json()
    refund = acme_payments.refund(charge_id, amount_cents)
    return {"invoice": invoice_id, "order": order.get("id"), "refund": refund}
