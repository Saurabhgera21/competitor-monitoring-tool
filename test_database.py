
import pytest

import database


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Use a separate temporary database for every test."""
    test_database_path = tmp_path / "test_competitor_monitor.db"

    monkeypatch.setattr(
        database,
        "DATABASE_NAME",
        str(test_database_path),
    )

    database.create_database()
    return test_database_path


def test_new_article_is_saved(test_db):
    articles = [
        {
            "title": "AI Marketing Guide",
            "url": "https://example.com/blog/ai-marketing",
            "description": "A guide to AI marketing.",
        }
    ]

    result = database.save_articles("example.com", articles)

    assert len(result) == 1
    assert result[0]["title"] == "AI Marketing Guide"

    saved_articles = database.get_articles("example.com")
    assert len(saved_articles) == 1


def test_duplicate_article_is_not_saved_twice(test_db):
    article = {
        "title": "AI Marketing Guide",
        "url": "https://example.com/blog/ai-marketing",
        "description": "A guide to AI marketing.",
    }

    first_scan = database.save_articles("example.com", [article])
    second_scan = database.save_articles("example.com", [article])

    assert len(first_scan) == 1
    assert len(second_scan) == 0
    assert len(database.get_articles("example.com")) == 1


def test_article_without_url_is_skipped(test_db):
    articles = [
        {
            "title": "Article without a URL",
            "description": "This should not be saved.",
        }
    ]

    result = database.save_articles("example.com", articles)

    assert result == []
    assert database.get_articles("example.com") == []


def test_first_price_scan_creates_baseline(test_db):
    pricing_items = [
        {
            "url": "https://example.com/pricing",
            "product_name": "Basic",
            "price": "₹999/month",
        }
    ]

    changes = database.save_pricing_data(
        "example.com",
        pricing_items,
    )

    assert changes == []

    saved_prices = database.get_current_prices("example.com")
    assert len(saved_prices) == 1
    assert saved_prices[0]["price"] == "₹999/month"


def test_price_change_is_detected(test_db):
    original_price = [
        {
            "url": "https://example.com/pricing",
            "product_name": "Basic",
            "price": "₹999/month",
        }
    ]

    updated_price = [
        {
            "url": "https://example.com/pricing",
            "product_name": "Basic",
            "price": "₹1,199/month",
        }
    ]

    database.save_pricing_data("example.com", original_price)

    changes = database.save_pricing_data(
        "example.com",
        updated_price,
    )

    assert len(changes) == 1
    assert changes[0]["old_price"] == "₹999/month"
    assert changes[0]["new_price"] == "₹1,199/month"

    current_prices = database.get_current_prices("example.com")
    assert current_prices[0]["price"] == "₹1,199/month"

    history = database.get_pricing_changes("example.com")
    assert len(history) == 1


def test_unchanged_price_does_not_create_change(test_db):
    pricing_items = [
        {
            "url": "https://example.com/pricing",
            "product_name": "Basic",
            "price": "₹999/month",
        }
    ]

    database.save_pricing_data("example.com", pricing_items)

    changes = database.save_pricing_data(
        "example.com",
        pricing_items,
    )

    assert changes == []
    assert database.get_pricing_changes("example.com") == []
