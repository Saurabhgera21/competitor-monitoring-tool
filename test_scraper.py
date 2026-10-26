
from unittest.mock import patch

from scraper import scrape_website


def test_scrape_website_handles_invalid_url():
    articles, error = scrape_website("not-a-valid-url")

    assert error is not None or articles == []


def test_scrape_website_handles_no_articles():
    fake_html = """
    <html>
        <head><title>Test Website</title></head>
        <body><p>This page has no articles.</p></body>
    </html>
    """

    with patch("scraper.get_html", return_value=fake_html):
        articles, error = scrape_website("https://example.com")

    assert error is None or articles == []


def test_scrape_website_handles_blocked_website():
    with patch("scraper.get_html", return_value=None):
        articles, error = scrape_website("https://example.com")

    assert error is not None or articles == []
