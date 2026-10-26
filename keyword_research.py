
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.keywordseverywhere.com/v1/get_keyword_data"


def get_keyword_data(keyword, country="in", currency="inr"):
    """
    Fetch search volume and SEO metrics for one keyword.

    Returns a dictionary containing the keyword metrics or an error.
    """

    api_key = os.getenv("KEYWORDS_EVERYWHERE_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "API key missing. Check your .env file.",
        }

    keyword = keyword.strip()

    if not keyword:
        return {
            "success": False,
            "error": "Please enter a keyword.",
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    payload = {
        "dataSource": "gkp",
        "country": country,
        "currency": currency,
        "kw[]": keyword,
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            data=payload,
            timeout=20,
        )

        if response.status_code == 401:
            return {
                "success": False,
                "error": "API key is invalid or unauthorized.",
            }

        if response.status_code == 402:
            return {
                "success": False,
                "error": "API credits or an active plan may be required.",
            }

        if response.status_code == 429:
            return {
                "success": False,
                "error": "API rate limit reached. Please try again later.",
            }

        response.raise_for_status()
        result = response.json()

        if "data" not in result:
            return {
                "success": False,
                "error": result.get(
                    "message",
                    "The API did not return keyword data.",
                ),
            }

        if not result["data"]:
            return {
                "success": False,
                "error": "No keyword data was returned.",
            }

        item = result["data"][0]

        cpc_data = item.get("cpc") or {}
        trend_data = item.get("trend") or []

        return {
            "success": True,
            "keyword": item.get("keyword", keyword),
            "search_volume": item.get("vol"),
            "cpc": cpc_data.get("value"),
            "cpc_currency": cpc_data.get("currency"),
            "competition": item.get("competition"),
            "trend": trend_data,
            "credits_used": result.get("credits_consumed"),
            "credits_remaining": result.get("credits"),
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "The keyword API timed out. Please try again.",
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Could not connect to the keyword API.",
        }

    except requests.exceptions.HTTPError as exc:
        return {
            "success": False,
            "error": f"Keyword API request failed: {exc}",
        }

    except (ValueError, KeyError, TypeError) as exc:
        return {
            "success": False,
            "error": f"Could not read the API response: {exc}",
        }

    except requests.exceptions.RequestException as exc:
        return {
            "success": False,
            "error": f"Keyword API error: {exc}",
        }
