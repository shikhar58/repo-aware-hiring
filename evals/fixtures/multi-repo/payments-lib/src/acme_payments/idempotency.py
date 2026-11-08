import hashlib
import time


def idempotency_key(customer_id: str, amount_cents: int, window_s: int = 60) -> str:
    bucket = int(time.time() // window_s)
    return hashlib.sha256(f"{customer_id}:{amount_cents}:{bucket}".encode()).hexdigest()[:32]
