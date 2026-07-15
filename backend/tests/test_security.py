"""SSRF guard tests: redirects are re-checked hop-by-hop before being fetched."""
from __future__ import annotations

import httpx
import pytest
from app.core import security
from app.core.security import MAX_REDIRECTS, SSRFBlocked, assert_public_http, safe_fetch_text

# hostname -> resolved IP (no real DNS in tests)
FAKE_DNS = {
    "public.test": "93.184.216.34",
    "public2.test": "8.8.8.8",
    "internal.test": "127.0.0.1",
    "metadata.test": "169.254.169.254",
}


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch):
    def fake_getaddrinfo(host, port, *args, **kwargs):
        if host in FAKE_DNS:
            return [(2, 1, 6, "", (FAKE_DNS[host], 0))]
        raise security.socket.gaierror(f"unknown test host: {host}")
    monkeypatch.setattr(security.socket, "getaddrinfo", fake_getaddrinfo)


def _transport(routes: dict[str, httpx.Response]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return routes[str(request.url)]
    return httpx.MockTransport(handler)


def test_assert_public_http_blocks_private_hosts():
    for bad in ("http://internal.test/", "http://metadata.test/latest", "ftp://public.test/a"):
        with pytest.raises(SSRFBlocked):
            assert_public_http(bad)
    assert_public_http("https://public.test/")  # public passes


def test_redirect_to_private_ip_is_blocked_before_fetch():
    fetched = []

    def handler(request: httpx.Request) -> httpx.Response:
        fetched.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://internal.test/secrets"})

    with pytest.raises(SSRFBlocked):
        safe_fetch_text("http://public.test/", transport=httpx.MockTransport(handler))
    # the private target must never have been requested
    assert fetched == ["http://public.test/"]


def test_redirect_to_metadata_ip_is_blocked():
    t = _transport({"http://public.test/": httpx.Response(
        301, headers={"location": "http://metadata.test/latest/meta-data/"})})
    with pytest.raises(SSRFBlocked):
        safe_fetch_text("http://public.test/", transport=t)


def test_public_redirect_chain_is_followed():
    t = _transport({
        "http://public.test/": httpx.Response(302, headers={"location": "http://public2.test/page"}),
        "http://public2.test/page": httpx.Response(200, text="hello lead"),
    })
    assert safe_fetch_text("http://public.test/", transport=t) == "hello lead"


def test_relative_redirect_is_resolved_and_followed():
    t = _transport({
        "http://public.test/": httpx.Response(302, headers={"location": "/contact"}),
        "http://public.test/contact": httpx.Response(200, text="contact page"),
    })
    assert safe_fetch_text("http://public.test/", transport=t) == "contact page"


def test_too_many_redirects_blocked():
    def handler(request: httpx.Request) -> httpx.Response:  # infinite public loop
        return httpx.Response(302, headers={"location": "http://public.test/"})

    with pytest.raises(SSRFBlocked, match="too many redirects"):
        safe_fetch_text("http://public.test/", transport=httpx.MockTransport(handler))
    assert MAX_REDIRECTS == 5


def test_body_is_capped(monkeypatch):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "MAX_FETCH_BYTES", 10)
    t = _transport({"http://public.test/": httpx.Response(200, text="x" * 100)})
    assert safe_fetch_text("http://public.test/", transport=t) == "x" * 10
