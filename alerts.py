
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_slack_alert(message):
    """Send an alert message to the configured Slack channel."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "").strip()

    if not webhook_url:
        return False, "Slack webhook URL is missing from .env."

    try:
        response = requests.post(
            webhook_url,
            json={"text": message},
            timeout=15,
        )

        if response.status_code == 200 and response.text == "ok":
            return True, "Slack alert sent successfully."

        return False, (
            f"Slack rejected the message: "
            f"HTTP {response.status_code}."
        )

    except requests.RequestException as exc:
        return False, f"Could not send Slack alert: {exc}"
