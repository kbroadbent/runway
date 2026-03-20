from unittest.mock import patch, MagicMock
from app.services.research_service import generate_research_links, scrape_levels_fyi


def test_generate_research_links():
    links = generate_research_links("Acme Corp")
    assert "glassdoor" in links["glassdoor_url"].lower()
    assert "levels.fyi" in links["levels_url"].lower() or "levelsfyi" in links["levels_url"].lower()
    assert "blind" in links["blind_url"].lower()
    assert "Acme" in links["glassdoor_url"] or "acme" in links["glassdoor_url"].lower()


def test_generate_links_encodes_special_chars():
    links = generate_research_links("Ben & Jerry's")
    assert "&" not in links["glassdoor_url"].split("?")[0] or "%26" in links["glassdoor_url"]


def test_scrape_levels_fyi_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '<div>Some salary data</div>'
    with patch("app.services.research_service.httpx.get", return_value=mock_resp):
        result = scrape_levels_fyi("Google")
    import json
    assert result is not None
    assert "url" in json.loads(result)


def test_scrape_levels_fyi_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    with patch("app.services.research_service.httpx.get", return_value=mock_resp):
        result = scrape_levels_fyi("Google")
    assert result is None
