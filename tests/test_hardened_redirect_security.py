"""H002 / FU-002 credential redirect invariant regression tests."""

from __future__ import annotations

from urllib.request import Request

import pytest

from lib import http


ALL_CREDENTIAL_HEADERS = {
    "Authorization": "Bearer sentinel",
    "Proxy-Authorization": "Basic sentinel",
    "Cookie": "session=sentinel",
    "Cookie2": "session=sentinel",
    "Api-Key": "sentinel",
    "X-Api-Key": "sentinel",
    "X-Auth-Token": "sentinel",
    "X-CSRF-Token": "sentinel",
    "X-CSRFToken": "sentinel",
    "X-XSRF-Token": "sentinel",
    "Subscription-Key": "sentinel",
    "Ocp-Apim-Subscription-Key": "sentinel",
    "X-Subscription-Token": "sentinel",
    "X-Future-Provider-Token": "sentinel",
    "X-Custom-Authority": "Bearer sentinel",
}


def _redirect(src: str, dst: str, headers: dict[str, str]):
    handler = http._StripAuthOnCrossOriginRedirect()
    return handler.redirect_request(Request(src, headers=headers), None, 302, "Found", {}, dst)


def _headers(request: Request) -> dict[str, str]:
    merged: dict[str, str] = {}
    for store in (request.headers, request.unredirected_hdrs):
        merged.update({name.lower(): value for name, value in store.items()})
    return merged


def test_h002_cross_origin_strips_complete_credential_class():
    """TEST_ID=H002-REDIRECT-001."""
    redirected = _redirect(
        "https://api.example.test/start",
        "https://other.example.test/result",
        {**ALL_CREDENTIAL_HEADERS, "Accept": "application/json"},
    )
    observed = _headers(redirected)
    assert observed["accept"] == "application/json"
    for name in ALL_CREDENTIAL_HEADERS:
        assert name.lower() not in observed


def test_h002_same_origin_effective_port_preserves_credentials():
    """TEST_ID=H002-REDIRECT-002."""
    redirected = _redirect(
        "https://API.EXAMPLE.TEST/start",
        "https://api.example.test:443/result",
        ALL_CREDENTIAL_HEADERS,
    )
    observed = _headers(redirected)
    assert set(name.lower() for name in ALL_CREDENTIAL_HEADERS) <= set(observed)


@pytest.mark.parametrize(
    ("source", "destination"),
    [
        ("https://api.example.test/start", "https://api.example.test:8443/result"),
        ("http://localhost/start", "http://127.0.0.1/result"),
        ("http://127.0.0.1/start", "http://[::1]/result"),
        ("http://127.0.0.1:8080/start", "http://127.0.0.1:8081/result"),
        ("http://api.example.test/start", "https://api.example.test/result"),
    ],
)
def test_h002_origin_change_strips_credentials(source: str, destination: str):
    """TEST_ID=H002-REDIRECT-003."""
    assert "authorization" not in _headers(
        _redirect(source, destination, {"Authorization": "Bearer sentinel"})
    )


def test_h002_each_redirect_hop_rechecks_origin():
    """TEST_ID=H002-REDIRECT-004."""
    first = _redirect(
        "https://one.example.test/start",
        "https://one.example.test:443/middle",
        {"Authorization": "Bearer sentinel", "Accept": "application/json"},
    )
    assert _headers(first)["authorization"] == "Bearer sentinel"
    second = http._StripAuthOnCrossOriginRedirect().redirect_request(
        first,
        None,
        302,
        "Found",
        {},
        "https://two.example.test/result",
    )
    assert "authorization" not in _headers(second)
    assert _headers(second)["accept"] == "application/json"


def test_h002_https_downgrade_is_blocked_not_merely_stripped():
    """TEST_ID=H002-REDIRECT-005."""
    with pytest.raises(http.UnsafeRedirectError, match="HTTPS downgrade"):
        _redirect(
            "https://api.example.test/start",
            "http://api.example.test/result",
            {"Authorization": "Bearer sentinel"},
        )


@pytest.mark.parametrize(
    "destination",
    [
        "https://user:password@api.example.test/result",
        "https://api.example.test:not-a-port/result",
        "//api.example.test/result",
        "file:///tmp/result",
        "https:///missing-host",
    ],
)
def test_h002_malformed_or_ambiguous_destination_fails_closed(destination: str):
    """TEST_ID=H002-REDIRECT-006."""
    with pytest.raises(http.UnsafeRedirectError):
        _redirect(
            "https://api.example.test/start",
            destination,
            {"Authorization": "Bearer sentinel"},
        )
