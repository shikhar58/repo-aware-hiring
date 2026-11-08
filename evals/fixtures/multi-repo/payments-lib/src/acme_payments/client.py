import httpx
from pydantic import BaseModel

from .idempotency import idempotency_key

PROVIDER_URL = "https://api.payments-provider.com/v1"


class Charge(BaseModel):
    id: str
    amount_cents: int
    currency: str
    status: str


class PaymentClient:
    def __init__(self, api_base: str = PROVIDER_URL, timeout: float = 5.0):
        self._http = httpx.Client(base_url=api_base, timeout=timeout)

    def charge(self, customer_id: str, amount_cents: int, currency: str = "EUR", key: str | None = None) -> Charge:
        key = key or idempotency_key(customer_id, amount_cents)
        r = self._http.post("/charges", json={"customer": customer_id, "amount": amount_cents, "currency": currency},
                            headers={"Idempotency-Key": key})
        r.raise_for_status()
        return Charge(**r.json())

    def refund(self, charge_id: str, amount_cents: int | None = None) -> dict:
        r = self._http.post(f"/charges/{charge_id}/refunds", json={"amount": amount_cents})
        r.raise_for_status()
        return r.json()


_default = None


def _client() -> PaymentClient:
    global _default
    if _default is None:
        _default = PaymentClient()
    return _default


def charge(customer_id: str, amount_cents: int, currency: str = "EUR") -> Charge:
    return _client().charge(customer_id, amount_cents, currency)


def refund(charge_id: str, amount_cents: int | None = None) -> dict:
    return _client().refund(charge_id, amount_cents)
