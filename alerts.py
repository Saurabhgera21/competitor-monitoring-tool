
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(name):
    """Read a secret from environment variables or Streamlit Cloud."""
    value = os.getenv(name, "").strip()

    if value:
        return value

    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def send_slack_alert(message):
    """Send an alert message to the configured Slack channel."""
    webhook_url = get_secret("SLACK_WEBHOOK_URL")

    if not webhook_url:
        return False, "Slack webhook URL is missing from configuration."

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
