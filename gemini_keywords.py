
import json
import os
import re
import time

import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAMES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def get_secret(name):
    """Read configuration from environment variables or Streamlit Secrets."""
    value = os.getenv(name, "").strip()

    if value:
        return value

    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def generate_keywords(title, description="", count=5):
    """Generate keyword suggestions, not verified search volumes."""

    api_key = get_secret("GEMINI_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "GEMINI_API_KEY is missing from the configuration.",
        }

    title = (title or "").strip()
    description = (description or "").strip()

    if not title:
        return {
            "success": False,
            "error": "An article title is required.",
        }

    prompt = f"""
Suggest up to {count} SEO keywords for this article.

Title: {title}
Description: {description[:1500]}

Return only valid JSON:
{{
  "keywords": [
    {{
      "keyword": "keyword phrase",
      "reason": "short explanation"
    }}
  ]
}}

Do not invent search-volume numbers.
Avoid duplicate or irrelevant keywords.
"""

    try:
        client = genai.Client(api_key=api_key)
        errors = []

        for model_name in MODEL_NAMES:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )

                    response_text = (response.text or "").strip()
                    response_text = re.sub(
                        r"^```(?:json)?\s*|\s*```$",
                        "",
                        response_text,
                        flags=re.IGNORECASE,
                    ).strip()

                    result = json.loads(response_text)
                    items = result.get("keywords", [])

                    cleaned = []
                    seen = set()

                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        keyword = str(item.get("keyword", "")).strip()
                        reason = str(item.get("reason", "")).strip()

                        if keyword and keyword.lower() not in seen:
                            seen.add(keyword.lower())
                            cleaned.append({
                                "keyword": keyword,
                                "reason": reason,
                            })

                    if not cleaned:
                        return {
                            "success": False,
                            "error": "Gemini returned no valid keywords.",
                        }

                    return {
                        "success": True,
                        "article_title": title,
                        "keywords": cleaned[:count],
                        "source": f"Gemini ({model_name})",
                        "search_volume": "Not available",
                    }

                except Exception as exc:
                    errors.append(f"{model_name}: {exc}")
                    error_text = str(exc)

                    if "503" in error_text or "UNAVAILABLE" in error_text:
                        if attempt == 0:
                            time.sleep(2)
                            continue

                    break

        return {
            "success": False,
            "error": (
                "All configured Gemini models failed. "
                "Check model availability, API access, and quota. "
                + " | ".join(errors[-2:])
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
