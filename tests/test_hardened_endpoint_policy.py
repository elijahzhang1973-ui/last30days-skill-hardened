"""H001 endpoint overrides have one strict policy at every provider edge."""

from __future__ import annotations

from urllib.parse import urlsplit

import pytest

from lib import permission_preflight, providers


PROVIDERS = (
    ("OPENAI_BASE_URL", providers.OPENAI_RESPONSES_URL),
    ("XAI_BASE_URL", providers.XAI_RESPONSES_URL),
    ("OPENROUTER_BASE_URL", providers.OPENROUTER_URL),
)

REJECTED = (
    "https://user@example.test/v1",
    "https://user:password@example.test/v1",
    "https://example.test:not-a-port/v1",
    "https://example.test:70000/v1",
    "https://example.test:/v1",
    "https://example.test:0/v1",
    "http://example.test/v1",
    "http://10.0.0.5:8080/v1",
    "//example.test/v1",
    "example.test/v1",
    "ftp://example.test/v1",
    "https:///missing-host",
    "https://example.test/v1#fragment",
    "https://example.test\\@attacker.test/v1",
    " https://example.test/v1",
    "https://example.test/v1\n",
)

ALLOWED = (
    "https://example.test/v1",
    "https://example.test:8443/v1?tenant=one",
    "http://localhost:4000/v1",
    "http://127.0.0.1:4000/v1",
    "http://127.0.0.2:4000/v1",
    "http://[::1]:4000/v1",
)


@pytest.mark.parametrize("key,default", PROVIDERS)
@pytest.mark.parametrize("value", REJECTED)
def test_h001_rejects_ambiguous_or_unsafe_endpoint_for_every_provider(
    key: str, default: str, value: str, monkeypatch, capsys
) -> None:
    monkeypatch.setenv(key, value)
    assert providers.resolve_endpoint(key, default) == default
    warning = capsys.readouterr().err
    assert key in warning
    assert value not in warning
    assert "userinfo" in warning
    assert "cleartext" in warning


@pytest.mark.parametrize("key,default", PROVIDERS)
@pytest.mark.parametrize("value", ALLOWED)
def test_h001_allows_https_and_loopback_http_for_every_provider(
    key: str, default: str, value: str, monkeypatch
) -> None:
    monkeypatch.setenv(key, value)
    resolved = providers.resolve_endpoint(key, default)
    expected_parts = urlsplit(value)
    resolved_parts = urlsplit(resolved)
    assert resolved != default
    assert resolved_parts.scheme == expected_parts.scheme
    assert resolved_parts.netloc == expected_parts.netloc
    assert resolved_parts.path.startswith(expected_parts.path.rstrip("/"))
    assert resolved_parts.query == expected_parts.query


@pytest.mark.parametrize("key,default", PROVIDERS)
def test_h001_preflight_and_runtime_share_the_same_rejection(
    key: str, default: str, monkeypatch
) -> None:
    secret = "dummy-secret-never-report"
    value = f"https://user:{secret}@gateway.example/v1?token={secret}"
    monkeypatch.setenv(key, value)
    preflight = permission_preflight.build(
        {key: value}, {"ignored_endpoint_overrides": [], "safe": True}
    )
    assert preflight["network"]["endpoint_overrides"] == []
    assert preflight["network"]["ignored_endpoint_overrides"] == [key]
    assert secret not in str(preflight)
    assert providers.resolve_endpoint(key, default) == default


@pytest.mark.parametrize(
    "value",
    (
        "http://localhost:4000/v1",
        "http://127.0.0.1:4000/v1",
        "http://127.0.0.2:4000/v1",
        "http://[::1]:4000/v1",
    ),
)
def test_h001_loopback_http_is_the_only_proxy_bypass_class(value: str) -> None:
    assert providers.allowed_base_url_override(value)
    assert providers.is_loopback_http_endpoint(value)
    assert not providers.is_loopback_http_endpoint("https://example.test/v1")
