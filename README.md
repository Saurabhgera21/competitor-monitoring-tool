# Competitor Monitoring Tool

A Python and Streamlit application that monitors competitor websites for new articles and pricing changes, with keyword suggestions and Slack notifications.

## Features

- **Competitor Monitoring:** Scan websites for articles and content updates.
- **New Article Detection:** Store previously discovered articles and identify new ones during subsequent scans.
- **Pricing Monitoring:** Track observed prices and detect changes.
- **AI Keyword Suggestions:** Use Google's Gemini API to suggest relevant keywords for articles.
- **Slack Alerts:** Send notifications when new articles or pricing changes are detected.
- **SQLite Database:** Store articles, current prices, and pricing-change history.
- **Automated Tests:** Test database operations, scraping behavior, and Slack alerts.

## Tech Stack

- Python
- Streamlit
- Beautiful Soup
- SQLite
- Google Gemini API
- Slack Incoming Webhooks
- Pytest

## Project Structure

```text
competitor-monitoring-tool/
├── app.py
├── scraper.py
├── database.py
├── alerts.py
├── gemini_keywords.py
├── keyword_research.py
├── requirements.txt
├── .gitignore
├── test_app.py
├── test_streamlit.py
├── test_scraper.py
├── test_database.py
└── test_alerts.py
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Saurabhgera21/competitor-monitoring-tool.git
   cd competitor-monitoring-tool
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows:

   ```bat
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root. Add your own API credentials and Slack webhook URL:

```env
GEMINI_API_KEY=your_gemini_api_key
KEYWORDS_EVERYWHERE_API_KEY=your_keywords_everywhere_api_key
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

Replace the placeholder values with your own credentials. Never commit `.env` or expose API keys in screenshots or public code.

Some integrations may require an active API plan or available credits.

## Run the Application

```bash
streamlit run app.py
```

Streamlit will provide a local URL to open the application in your browser.

## Run Tests

```bash
python -m pytest -v
```

## Limitations

- Website scraping depends on each website's structure, availability, and anti-bot protections.
- Keyword suggestions do not guarantee verified search-volume data.
- Slack notifications require a valid webhook.
- The local SQLite database is intended for local use; hosted deployments may need persistent database storage.

## Future Improvements

- Add more reliable scheduling for automatic scans.
- Improve support for different website structures.
- Integrate a verified keyword search-volume provider.
- Add persistent database storage for hosted deployments.
- Improve monitoring and alert configuration.

## Author

**Saurabh Gera**

GitHub: [@Saurabhgera21](https://github.com/Saurabhgera21)
