from acme_payments.idempotency import idempotency_key


def test_key_is_stable_within_window():
    assert idempotency_key("c1", 500) == idempotency_key("c1", 500)
