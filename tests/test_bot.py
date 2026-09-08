import unittest
import os
import tempfile
from filters.priority_filter import analyze_article, extract_tickers
from database import init_db, is_article_processed, mark_article_processed, get_recent_articles
from bot.telegram_notifier import format_alert_card

class TestPriorityFilter(unittest.TestCase):
    def test_fed_keyword_categorization(self):
        title = "Federal Reserve Announces 50 Bps Interest Rate Cut"
        res = analyze_article(title)
        self.assertTrue(res["is_relevant"])
        self.assertEqual(res["category"], "FED")
        self.assertEqual(res["urgency"], "HIGH")

    def test_ma_keyword_categorization(self):
        title = "Company X Agrees to Acquire Company Y in $10B Merger Deal"
        res = analyze_article(title)
        self.assertTrue(res["is_relevant"])
        self.assertEqual(res["category"], "M&A")
        self.assertEqual(res["urgency"], "HIGH")

    def test_ticker_extraction(self):
        text = "Acquisition announcement for $AAPL and $NVDA regarding quarterly growth"
        tickers = extract_tickers(text)
        self.assertIn("$AAPL", tickers)
        self.assertIn("$NVDA", tickers)

class TestDatabaseOps(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.close(self.db_fd)
        init_db(self.db_path)

    def tearDown(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            wal_path = f"{self.db_path}-wal"
            shm_path = f"{self.db_path}-shm"
            if os.path.exists(wal_path):
                os.remove(wal_path)
            if os.path.exists(shm_path):
                os.remove(shm_path)
        except PermissionError:
            pass

    def test_article_deduplication(self):
        article_id = "test_hash_123"
        self.assertFalse(is_article_processed(article_id, self.db_path))

        mark_article_processed(
            article_id,
            "Test Fed Title",
            "https://example.com/fed",
            "Federal Reserve",
            "FED",
            "2026-09-07",
            self.db_path
        )

        self.assertTrue(is_article_processed(article_id, self.db_path))
        recent = get_recent_articles(limit=5, db_path=self.db_path)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["title"], "Test Fed Title")

class TestTelegramNotifier(unittest.TestCase):
    def test_format_card(self):
        article = {
            "badge": "🏛️ FED ANNOUNCEMENT",
            "title": "FOMC Interest Rate Decision",
            "summary": "Fed cuts benchmark rate.",
            "url": "https://example.com/news",
            "source": "Federal Reserve",
            "published_at": "Mon, 07 Sep 2026",
            "tickers": ["$AAPL"]
        }
        card = format_alert_card(article)
        self.assertIn("FOMC Interest Rate Decision", card)
        self.assertIn("🏛️ FED ANNOUNCEMENT", card)
        self.assertIn("#AAPL", card)

if __name__ == "__main__":
    unittest.main()
