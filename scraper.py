
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36"
    )
}

ARTICLE_PATHS = (
    "/blog/", "/blogs/", "/article/", "/articles/",
    "/resources/", "/posts/", "/news/"
)

SKIP_PATHS = (
    "/topics/", "/topic/", "/tag/", "/tags/",
    "/category/", "/categories/", "/author/", "/authors/"
)

PRICE_PATHS = (
    "/pricing", "/plans", "/price", "/membership"
)

TIMEOUT = 8
MAX_LISTING_PAGES = 3
MAX_ARTICLES = 10
MAX_PRICING_PAGES = 3


def normalize_url(url):
    url = urldefrag(url)[0]
    parsed = urlparse(url)

    if parsed.path != "/":
        url = url.rstrip("/")

    return url


def same_domain(url, base_domain):
    host = urlparse(url).netloc.lower().split(":")[0]
    base = base_domain.lower().split(":")[0]

    return host.removeprefix("www.") == base.removeprefix("www.")


def is_skipped(path):
    return any(part in path.lower() for part in SKIP_PATHS)


def is_article_path(path):
    return any(part in path.lower() for part in ARTICLE_PATHS)


def get_html(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()

        if "html" not in response.headers.get(
            "Content-Type", "text/html"
        ).lower():
            return None

        return response.text

    except requests.RequestException:
        return None


def extract_article(url):
    html = get_html(url)

    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    title_tag = soup.find("title")

    title = (
        h1.get_text(" ", strip=True)
        if h1 else (
            title_tag.get_text(" ", strip=True)
            if title_tag else ""
        )
    )

    if not title or title.lower() in {
        "blog", "blogs", "guides", "articles",
        "resources", "news", "insights"
    }:
        return None

    description_tag = soup.find(
        "meta", attrs={"name": "description"}
    )

    description = (
        description_tag.get("content", "").strip()
        if description_tag else ""
    )

    date_tag = (
        soup.find("meta", property="article:published_time")
        or soup.find("meta", attrs={"name": "date"})
        or soup.find("time", attrs={"datetime": True})
    )

    published_date = ""

    if date_tag:
        published_date = (
            date_tag.get("content", "")
            or date_tag.get("datetime", "")
            or date_tag.get_text(" ", strip=True)
        ).strip()

    return {
        "title": title,
        "url": url,
        "description": description,
        "published_date": published_date,
    }


def extract_prices(url):
    """Extract plan prices from pricing-page text."""
    html = get_html(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

    # Match the plan name and price together.
    pattern = re.compile(
        r"\b(Basic|Grow|Advanced|Plus|Starter|Shopify|"
        r"Enterprise|POS Pro)\b"
        r"\s+(?:from\s+)?"
        r"((?:₹|US\$|CA\$|AU\$|[$€£])\s*"
        r"[\d,]+(?:\.\d{1,2})?)"
        r"(?:\s*/?\s*(mo|month|yr|year))?",
        re.IGNORECASE
    )

    pricing_items = []
    seen = set()

    for match in pattern.finditer(text):
        name = match.group(1).strip()
        price = match.group(2).strip()

        if match.group(3):
            price += "/" + match.group(3).lower()

        key = (name.lower(), price.lower())

        if key not in seen:
            seen.add(key)
            pricing_items.append({
                "url": url,
                "product_name": name,
                "price": price
            })

    # Fallback: detect currency amounts even if plan names
    # are separated from prices by website layout text.
    if not pricing_items:
        price_pattern = re.compile(
            r"(₹|US\$|CA\$|AU\$|[$€£])\s*"
            r"([\d,]+(?:\.\d{1,2})?)"
            r"\s*/?\s*(mo|month|yr|year)?",
            re.IGNORECASE
        )

        for index, match in enumerate(
            price_pattern.finditer(text), start=1
        ):
            amount = match.group(1) + match.group(2)

            if match.group(3):
                amount += "/" + match.group(3).lower()

            pricing_items.append({
                "url": url,
                "product_name": f"Pricing option {index}",
                "price": amount
            })

            if len(pricing_items) >= 20:
                break

    return pricing_items


def scrape_pricing_pages(domain):
    """Discover and inspect pricing pages."""
    domain = domain.strip()

    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain

    homepage_html = get_html(domain)

    if not homepage_html:
        return []

    base_domain = urlparse(domain).netloc
    soup = BeautifulSoup(homepage_html, "html.parser")
    pricing_urls = []

    for link in soup.find_all("a", href=True):
        url = normalize_url(urljoin(domain, link["href"]))
        path = urlparse(url).path.lower()
        link_text = link.get_text(" ", strip=True).lower()

        if not same_domain(url, base_domain):
            continue

        if (
            any(part in path for part in PRICE_PATHS)
            or "pricing" in link_text
            or "plans" in link_text
        ):
            if url not in pricing_urls:
                pricing_urls.append(url)

    if not pricing_urls:
        for path in ("/pricing", "/plans"):
            url = urljoin(domain, path)

            if get_html(url):
                pricing_urls.append(url)

    results = []

    for url in pricing_urls[:MAX_PRICING_PAGES]:
        results.extend(extract_prices(url))

    return results


def scrape_website(domain):
    """Discover articles and pricing information for a domain."""
    domain = domain.strip()

    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain

    homepage_html = get_html(domain)

    if not homepage_html:
        return None, (
            "Could not access this website. "
            "It may be unavailable or blocking automated requests."
        )

    base_domain = urlparse(domain).netloc
    soup = BeautifulSoup(homepage_html, "html.parser")

    article_urls = set()
    listing_urls = []

    for link in soup.find_all("a", href=True):
        url = normalize_url(urljoin(domain, link["href"]))
        path = urlparse(url).path.lower()
        link_text = link.get_text(" ", strip=True).lower()

        if not same_domain(url, base_domain):
            continue

        if is_skipped(path):
            continue

        if is_article_path(path):
            article_urls.add(url)

        elif any(
            word in path + " " + link_text
            for word in ["blog", "articles", "resources", "news"]
        ):
            if url not in listing_urls:
                listing_urls.append(url)

    for listing_url in listing_urls[:MAX_LISTING_PAGES]:
        html = get_html(listing_url)

        if not html:
            continue

        listing_soup = BeautifulSoup(html, "html.parser")

        for link in listing_soup.find_all("a", href=True):
            url = normalize_url(urljoin(listing_url, link["href"]))
            path = urlparse(url).path.lower()

            if (
                same_domain(url, base_domain)
                and is_article_path(path)
                and not is_skipped(path)
            ):
                article_urls.add(url)

    articles = []

    for url in sorted(article_urls)[:MAX_ARTICLES]:
        article = extract_article(url)

        if article:
            articles.append(article)

    pricing_items = scrape_pricing_pages(domain)

    return {
        "articles": articles,
        "pricing_items": pricing_items,
    }, None
