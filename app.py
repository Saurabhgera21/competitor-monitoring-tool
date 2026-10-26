
import streamlit as st

from database import (
    create_database,
    save_articles,
    get_articles,
    get_tracked_competitors,
    save_pricing_data,
    get_current_prices,
    get_pricing_changes,
)
from scraper import scrape_website
from gemini_keywords import generate_keywords
from alerts import send_slack_alert


# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------

st.set_page_config(
    page_title="Competitor Monitoring Alert Tool",
    page_icon="🔎",
    layout="wide",
)

create_database()

# Initialize session state.
defaults = {
    "new_articles": [],
    "new_price_changes": [],
    "last_domain": "",
    "scan_message": "",
    "scan_error": "",
    "keyword_results": {},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("🔎 Competitor Monitor")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Competitors",
        "Saved Articles",
        "Pricing History",
        "Settings",
    ],
)

st.title("🔎 Competitor Monitoring Alert Tool")
st.caption("Monitor competitor articles, pricing, and SEO keywords.")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":

    st.header("Dashboard")

    try:
        competitors = get_tracked_competitors()
        all_changes = get_pricing_changes()
    except Exception as exc:
        st.error(f"Could not load dashboard data: {exc}")
        st.stop()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "New articles this check",
        len(st.session_state.new_articles),
    )

    col2.metric(
        "Pricing changes detected",
        len(st.session_state.new_price_changes),
    )

    col3.metric(
        "Tracked websites",
        len(competitors),
    )

    st.divider()
    st.subheader("Add or scan a competitor")

    with st.form("competitor_scan_form"):

        domain = st.text_input(
            "Competitor website",
            placeholder="https://www.shopify.com",
        )

        submitted = st.form_submit_button(
            "Scan website",
            type="primary",
        )

    if submitted:

        if not domain.strip():
            st.warning("Please enter a competitor website.")

        else:
            normalized_domain = domain.strip()

            if not normalized_domain.startswith(
                ("http://", "https://")
            ):
                normalized_domain = "https://" + normalized_domain

            st.session_state.scan_error = ""
            st.session_state.scan_message = ""
            st.session_state.new_articles = []
            st.session_state.new_price_changes = []

            try:
                with st.spinner(
                    "Scanning articles and pricing pages. Please wait..."
                ):
                    results, error = scrape_website(normalized_domain)

                if error:
                    st.session_state.scan_error = error

                elif not isinstance(results, dict):
                    st.session_state.scan_error = (
                        "The scraper returned an unexpected result. "
                        "Please check scraper.py."
                    )

                else:
                    articles = results.get("articles", [])
                    pricing_items = results.get("pricing_items", [])

                    competitor_url = normalized_domain.rstrip("/")

                    # Save newly discovered articles.
                    new_articles = save_articles(
                        competitor_url,
                        articles,
                    )

                    # Save prices and detect price changes.
                    price_changes = save_pricing_data(
                        competitor_url,
                        pricing_items,
                    )

                    st.session_state.new_articles = new_articles
                    st.session_state.new_price_changes = price_changes
                    st.session_state.last_domain = competitor_url

                    st.session_state.scan_message = (
                        f"Scan complete: {len(new_articles)} new article(s), "
                        f"{len(price_changes)} price change(s), and "
                        f"{len(pricing_items)} price item(s) found."
                    )

                    # ------------------------------------------
                    # SEND SLACK ALERTS
                    # ------------------------------------------

                    if new_articles or price_changes:

                        alert_lines = [
                            "🔎 Competitor Monitoring Alert",
                            f"Website: {competitor_url}",
                            f"New articles: {len(new_articles)}",
                            f"Pricing changes: {len(price_changes)}",
                        ]

                        # Include up to five new articles.
                        for article in new_articles[:5]:
                            alert_lines.append(
                                f"\nNew article: "
                                f"{article.get('title', 'Untitled article')}"
                            )

                            article_url = article.get("url", "")

                            if article_url:
                                alert_lines.append(article_url)

                        # Include up to five pricing changes.
                        for change in price_changes[:5]:
                            alert_lines.append(
                                f"\nPrice change: "
                                f"{change.get('product_name', 'Product')}"
                            )

                            alert_lines.append(
                                f"{change.get('old_price', 'Unknown')} "
                                f"→ {change.get('new_price', 'Unknown')}"
                            )

                            price_url = change.get("url", "")

                            if price_url:
                                alert_lines.append(price_url)

                        try:
                            success, message = send_slack_alert(
                                "\n".join(alert_lines)
                            )

                            if success:
                                st.session_state.scan_message += (
                                    " Slack alert sent successfully."
                                )
                            else:
                                st.session_state.scan_error = (
                                    f"Slack notification failed: {message}"
                                )

                        except Exception as exc:
                            st.session_state.scan_error = (
                                f"Slack notification failed: {exc}"
                            )

            except Exception as exc:
                st.session_state.scan_error = (
                    f"Scan failed: {type(exc).__name__}: {exc}"
                )

    if st.session_state.scan_error:
        st.error(st.session_state.scan_error)

    if st.session_state.scan_message:
        st.success(st.session_state.scan_message)

    # ------------------------------------------
    # DISPLAY NEW ARTICLES
    # ------------------------------------------

    if st.session_state.new_articles:

        st.subheader("New articles found")

        for index, article in enumerate(
            st.session_state.new_articles
        ):

            article_title = article.get(
                "title",
                "Untitled article",
            )

            article_url = article.get("url", "")

            article_description = (
                article.get("description") or ""
            )

            st.markdown(f"### {article_title}")

            st.write(
                article_description or "No description available."
            )

            if article_url:
                st.markdown(f"[Read article]({article_url})")

            # Generate SEO keywords.
            if st.button(
                "🔑 Generate SEO Keywords",
                key=f"generate_keywords_{index}",
            ):

                with st.spinner(
                    "Gemini is generating keywords..."
                ):
                    keyword_result = generate_keywords(
                        article_title,
                        article_description,
                    )

                st.session_state.keyword_results[
                    article_url or article_title
                ] = keyword_result

            # Display generated keywords.
            result_key = article_url or article_title

            keyword_result = st.session_state.keyword_results.get(
                result_key
            )

            if keyword_result:

                if keyword_result.get("success"):

                    st.markdown("**Suggested SEO Keywords**")

                    for item in keyword_result.get("keywords", []):
                        st.markdown(
                            f"- **{item.get('keyword', '')}**"
                        )

                        st.caption(item.get("reason", ""))

                    st.caption(
                        "Generated by: "
                        f"{keyword_result.get('source', 'Gemini')}"
                    )

                    st.info(
                        "Monthly search volume: Not available. "
                        "These are AI-generated keyword suggestions, "
                        "not verified search-volume data."
                    )

                else:
                    st.error(
                        keyword_result.get(
                            "error",
                            "Keyword generation failed.",
                        )
                    )

            st.divider()

    # ------------------------------------------
    # DISPLAY PRICE CHANGES
    # ------------------------------------------

    if st.session_state.new_price_changes:

        st.subheader("Price changes found")

        for change in st.session_state.new_price_changes:

            st.write(
                f"**{change.get('product_name', 'Product')}**: "
                f"{change.get('old_price', 'Unknown')} "
                f"→ {change.get('new_price', 'Unknown')}"
            )

            if change.get("url"):
                st.markdown(
                    f"[Open pricing page]({change['url']})"
                )

    if (
        st.session_state.scan_message
        and not st.session_state.new_articles
        and not st.session_state.new_price_changes
    ):
        st.info(
            "No new articles or price changes were detected in this scan. "
            "Check Pricing History to see the currently observed prices."
        )


# --------------------------------------------------
# COMPETITORS PAGE
# --------------------------------------------------

elif page == "Competitors":

    st.header("Tracked Competitors")

    try:
        competitors = get_tracked_competitors()

        if competitors:
            for competitor in competitors:
                st.markdown(f"- 🌐 {competitor}")

        else:
            st.info(
                "No tracked competitors yet. Scan a website first."
            )

    except Exception as exc:
        st.error(f"Could not load competitors: {exc}")


# --------------------------------------------------
# SAVED ARTICLES PAGE
# --------------------------------------------------

elif page == "Saved Articles":

    st.header("Saved Articles")

    try:
        competitors = get_tracked_competitors()

        if not competitors:
            st.info("No saved articles yet.")

        else:
            selected_competitor = st.selectbox(
                "Choose a competitor",
                competitors,
            )

            articles = get_articles(selected_competitor)

            if articles:

                for index, article in enumerate(articles):

                    article_title = article.get(
                        "title",
                        "Untitled article",
                    )

                    article_url = article.get("url", "")

                    article_description = (
                        article.get("description") or ""
                    )

                    st.subheader(article_title)

                    if article_url:
                        st.markdown(
                            f"[Open article]({article_url})"
                        )

                    st.write(
                        article_description or "No description available."
                    )

                    st.caption(
                        f"First seen: {article['first_seen']}"
                    )

                    if st.button(
                        "🔑 Generate SEO Keywords",
                        key=f"saved_keywords_{index}",
                    ):

                        with st.spinner(
                            "Gemini is generating keywords..."
                        ):
                            result = generate_keywords(
                                article_title,
                                article_description,
                            )

                        st.session_state.keyword_results[
                            article_url or article_title
                        ] = result

                    result_key = article_url or article_title

                    keyword_result = (
                        st.session_state.keyword_results.get(result_key)
                    )

                    if keyword_result:

                        if keyword_result.get("success"):

                            st.markdown("**Suggested SEO Keywords**")

                            for item in keyword_result.get(
                                "keywords", []
                            ):
                                st.markdown(
                                    f"- **{item.get('keyword', '')}**"
                                )

                                st.caption(item.get("reason", ""))

                            st.caption(
                                "Generated by: "
                                f"{keyword_result.get('source', 'Gemini')}"
                            )

                            st.info(
                                "Monthly search volume: Not available. "
                                "AI-generated suggestions are not verified "
                                "search-volume measurements."
                            )

                        else:
                            st.error(
                                keyword_result.get(
                                    "error",
                                    "Keyword generation failed.",
                                )
                            )

                    st.divider()

            else:
                st.info(
                    "No articles saved for this competitor yet."
                )

    except Exception as exc:
        st.error(f"Could not load saved articles: {exc}")


# --------------------------------------------------
# PRICING HISTORY PAGE
# --------------------------------------------------

elif page == "Pricing History":

    st.header("Pricing History")

    try:
        competitors = get_tracked_competitors()

        if not competitors:
            st.info("Scan a competitor website first.")

        else:
            selected_competitor = st.selectbox(
                "Filter by competitor",
                ["All competitors"] + competitors,
            )

            if selected_competitor == "All competitors":

                prices = []

                for competitor in competitors:
                    prices.extend(
                        get_current_prices(competitor)
                    )

                changes = get_pricing_changes()

            else:
                prices = get_current_prices(
                    selected_competitor
                )

                changes = get_pricing_changes(
                    selected_competitor
                )

            st.subheader("Current observed prices")

            if prices:

                for item in prices:

                    st.markdown(
                        f"**{item['product_name']} — "
                        f"{item['price']}**"
                    )

                    if item.get("url"):
                        st.markdown(
                            f"[Open pricing page]({item['url']})"
                        )

                    st.caption(
                        f"Last checked: {item['last_checked']}"
                    )

                    st.divider()

            else:
                st.info(
                    "No prices are saved yet. Run a new scan to collect "
                    "the first price observations."
                )

            st.subheader("Detected price changes")

            if changes:

                for change in changes:

                    st.markdown(
                        f"**{change['competitor']} — "
                        f"{change['product_name']}**"
                    )

                    st.write(
                        f"{change['old_price']} "
                        f"→ {change['new_price']}"
                    )

                    if change.get("url"):
                        st.markdown(
                            f"[Open pricing page]({change['url']})"
                        )

                    st.caption(
                        f"Detected: {change['detected_at']}"
                    )

                    st.divider()

            else:
                st.info(
                    "No price changes have been recorded yet."
                )

    except Exception as exc:
        st.error(f"Could not load pricing history: {exc}")


# --------------------------------------------------
# SETTINGS PAGE
# --------------------------------------------------

elif page == "Settings":

    st.header("Project Status")

    st.markdown("**Implemented**")

    st.write("- Article discovery and duplicate detection")
    st.write("- Article titles, descriptions, URLs, and date extraction")
    st.write("- Basic pricing-page discovery and price extraction")
    st.write("- SQLite storage for observed prices and price changes")
    st.write("- Dashboard, saved articles, and pricing history")
    st.write("- Gemini AI-generated SEO keyword suggestions")
    st.write("- Slack notifications for newly discovered articles")
    st.write("- Slack notifications for detected price changes")

    st.markdown("**Still to implement**")

    st.write("- Verified monthly search-volume API integration")
    st.write("- Automated tests across three real competitor websites")
    st.write("- Deployment and demo recording")

    st.caption(
        "Gemini suggests keywords but does not verify their monthly "
        "search volumes. Pricing extraction is heuristic, and some sites "
        "may not expose their prices in accessible HTML. Slack alerts "
        "require a valid SLACK_WEBHOOK_URL in your .env file."
    )
