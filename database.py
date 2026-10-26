
import sqlite3
from datetime import datetime

DATABASE_NAME = "competitor_monitor.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor TEXT NOT NULL,
                title TEXT,
                url TEXT NOT NULL,
                description TEXT,
                first_seen TEXT NOT NULL,
                UNIQUE(competitor, url)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS current_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor TEXT NOT NULL,
                url TEXT NOT NULL,
                product_name TEXT NOT NULL,
                price TEXT NOT NULL,
                last_checked TEXT NOT NULL,
                UNIQUE(competitor, url, product_name)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pricing_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor TEXT NOT NULL,
                url TEXT NOT NULL,
                product_name TEXT NOT NULL,
                old_price TEXT NOT NULL,
                new_price TEXT NOT NULL,
                detected_at TEXT NOT NULL
            )
        """)

        conn.commit()


def save_articles(competitor, articles):
    new_articles = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        for article in articles:
            url = article.get("url", "").strip()

            if not url:
                continue

            cursor = conn.execute("""
                INSERT OR IGNORE INTO articles
                (competitor, title, url, description, first_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (
                competitor,
                article.get("title", "Untitled article"),
                url,
                article.get("description", ""),
                now,
            ))

            if cursor.rowcount > 0:
                new_articles.append(article)

        conn.commit()

    return new_articles


def get_articles(competitor):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM articles
            WHERE competitor = ?
            ORDER BY first_seen DESC
        """, (competitor,)).fetchall()

    return [dict(row) for row in rows]


def get_all_articles():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM articles
            ORDER BY first_seen DESC
        """).fetchall()

    return [dict(row) for row in rows]


def remove_article(article_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM articles WHERE id = ?",
            (article_id,)
        )
        conn.commit()


def save_pricing_data(competitor, pricing_items):
    changes = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        for item in pricing_items:
            url = item.get("url", "").strip()
            product_name = item.get("product_name", "").strip()
            price = item.get("price", "").strip()

            if not url or not product_name or not price:
                continue

            existing = conn.execute("""
                SELECT price FROM current_prices
                WHERE competitor = ?
                AND url = ?
                AND product_name = ?
            """, (competitor, url, product_name)).fetchone()

            if existing is None:
                conn.execute("""
                    INSERT INTO current_prices
                    (competitor, url, product_name, price, last_checked)
                    VALUES (?, ?, ?, ?, ?)
                """, (competitor, url, product_name, price, now))

            elif existing["price"] != price:
                old_price = existing["price"]

                conn.execute("""
                    INSERT INTO pricing_changes
                    (competitor, url, product_name,
                     old_price, new_price, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    competitor, url, product_name,
                    old_price, price, now
                ))

                conn.execute("""
                    UPDATE current_prices
                    SET price = ?, last_checked = ?
                    WHERE competitor = ?
                    AND url = ?
                    AND product_name = ?
                """, (price, now, competitor, url, product_name))

                changes.append({
                    "competitor": competitor,
                    "url": url,
                    "product_name": product_name,
                    "old_price": old_price,
                    "new_price": price,
                    "detected_at": now,
                })

            else:
                conn.execute("""
                    UPDATE current_prices
                    SET last_checked = ?
                    WHERE competitor = ?
                    AND url = ?
                    AND product_name = ?
                """, (now, competitor, url, product_name))

        conn.commit()

    return changes


def get_current_prices(competitor):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM current_prices
            WHERE competitor = ?
            ORDER BY product_name
        """, (competitor,)).fetchall()

    return [dict(row) for row in rows]


def get_pricing_changes(competitor=None):
    with get_connection() as conn:
        if competitor:
            rows = conn.execute("""
                SELECT * FROM pricing_changes
                WHERE competitor = ?
                ORDER BY detected_at DESC
            """, (competitor,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM pricing_changes
                ORDER BY detected_at DESC
            """).fetchall()

    return [dict(row) for row in rows]


def get_tracked_competitors():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT competitor FROM articles
            UNION
            SELECT competitor FROM current_prices
            ORDER BY competitor
        """).fetchall()

    return [row["competitor"] for row in rows]
