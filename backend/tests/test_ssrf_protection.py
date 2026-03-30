"""Tests for SSRF protection in parser_service and the import endpoint."""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from app.services.parser_service import _validate_url, fetch_and_parse_url


# ---------------------------------------------------------------------------
# _validate_url — scheme validation
# ---------------------------------------------------------------------------

def test_validate_url_rejects_file_scheme():
    with pytest.raises(ValueError):
        _validate_url("file:///etc/passwd")


def test_validate_url_rejects_ftp_scheme():
    with pytest.raises(ValueError):
        _validate_url("ftp://example.com/file.txt")


def test_validate_url_rejects_javascript_scheme():
    with pytest.raises(ValueError):
        _validate_url("javascript:alert(1)")


def test_validate_url_rejects_data_scheme():
    with pytest.raises(ValueError):
        _validate_url("data:text/html,<h1>hi</h1>")


# ---------------------------------------------------------------------------
# _validate_url — RFC 1918 / loopback rejection
# ---------------------------------------------------------------------------

def test_validate_url_rejects_loopback_ip():
    with pytest.raises(ValueError):
        _validate_url("http://127.0.0.1/admin")


def test_validate_url_rejects_localhost():
    with pytest.raises(ValueError):
        _validate_url("http://localhost/admin")


def test_validate_url_rejects_rfc1918_10_block():
    with pytest.raises(ValueError):
        _validate_url("http://10.0.0.1/secret")


def test_validate_url_rejects_rfc1918_192_168_block():
    with pytest.raises(ValueError):
        _validate_url("http://192.168.1.100/secret")


def test_validate_url_rejects_rfc1918_172_16_block():
    with pytest.raises(ValueError):
        _validate_url("http://172.16.0.1/secret")


def test_validate_url_rejects_rfc1918_172_31_block():
    with pytest.raises(ValueError):
        _validate_url("http://172.31.255.255/secret")


def test_validate_url_rejects_all_zeros_ip():
    with pytest.raises(ValueError):
        _validate_url("http://0.0.0.0/secret")


# ---------------------------------------------------------------------------
# _validate_url — valid URLs pass
# ---------------------------------------------------------------------------

def test_validate_url_allows_https():
    # Should not raise
    _validate_url("https://example.com/jobs/123")


def test_validate_url_allows_http():
    # Should not raise
    _validate_url("http://example.com/jobs/123")


# ---------------------------------------------------------------------------
# fetch_and_parse_url — rejects invalid URLs before fetching
# ---------------------------------------------------------------------------

def test_fetch_and_parse_url_raises_on_private_ip():
    with pytest.raises(ValueError):
        fetch_and_parse_url("http://192.168.1.1/job")


def test_fetch_and_parse_url_raises_on_localhost():
    with pytest.raises(ValueError):
        fetch_and_parse_url("http://localhost:8000/internal")


def test_fetch_and_parse_url_raises_on_non_http_scheme():
    with pytest.raises(ValueError):
        fetch_and_parse_url("file:///etc/hosts")


# ---------------------------------------------------------------------------
# fetch_and_parse_url — rejects redirect to private IP
# ---------------------------------------------------------------------------

def test_fetch_and_parse_url_rejects_redirect_to_private_ip():
    """A redirect response pointing to a private IP must be blocked."""
    redirect_response = httpx.Response(
        status_code=301,
        headers={"Location": "http://192.168.1.1/internal"},
    )
    # The manual redirect loop should call _validate_url on the redirect target
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value = redirect_response
        mock_client.send.return_value = redirect_response

        with pytest.raises(ValueError):
            fetch_and_parse_url("https://jobs.example.com/posting/123")


# ---------------------------------------------------------------------------
# import endpoint — 400 for bad URL, 502 with fixed message for fetch failure
# ---------------------------------------------------------------------------

def test_import_endpoint_returns_400_for_invalid_url_scheme(client):
    resp = client.post("/api/postings/import", json={"url": "file:///etc/passwd"})
    assert resp.status_code == 400


def test_import_endpoint_returns_400_for_private_ip_url(client):
    resp = client.post("/api/postings/import", json={"url": "http://127.0.0.1/admin"})
    assert resp.status_code == 400


def test_import_endpoint_returns_502_with_fixed_message_on_fetch_failure(client):
    with patch("app.routers.postings.fetch_and_parse_url") as mock_fetch:
        mock_fetch.side_effect = httpx.ConnectError("Connection refused")
        resp = client.post("/api/postings/import", json={"url": "https://example.com/job"})
    assert resp.status_code == 502
    # The error message must be a fixed string, not expose raw exception details
    detail = resp.json()["detail"]
    assert "Connection refused" not in detail
    assert detail == "Could not fetch URL"


def test_import_endpoint_502_does_not_expose_exception_details(client):
    with patch("app.routers.postings.fetch_and_parse_url") as mock_fetch:
        mock_fetch.side_effect = httpx.ConnectError("internal host: metadata.google.internal")
        resp = client.post("/api/postings/import", json={"url": "https://example.com/job"})
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert "metadata.google.internal" not in detail
