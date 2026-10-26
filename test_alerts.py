
from unittest.mock import Mock, patch

import alerts


def test_missing_slack_webhook(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    success, message = alerts.send_slack_alert("Test message")

    assert success is False
    assert "missing" in message.lower()


@patch("alerts.requests.post")
def test_successful_slack_alert(mock_post, monkeypatch):
    monkeypatch.setenv(
        "SLACK_WEBHOOK_URL",
        "https://example.com/test-webhook",
    )

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "ok"
    mock_post.return_value = mock_response

    success, message = alerts.send_slack_alert("Test message")

    assert success is True
    assert "successfully" in message.lower()
    mock_post.assert_called_once()


@patch("alerts.requests.post")
def test_slack_rejection(mock_post, monkeypatch):
    monkeypatch.setenv(
        "SLACK_WEBHOOK_URL",
        "https://example.com/test-webhook",
    )

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "error"
    mock_post.return_value = mock_response

    success, message = alerts.send_slack_alert("Test message")

    assert success is False
    assert "500" in message
