def test_placeholder():
    assert True


def test_placeholder_host_is_not_a_service():
    url = "http://fake-ledger:9999"  # placeholder in a test: must not become a cross-repo link
    assert url
