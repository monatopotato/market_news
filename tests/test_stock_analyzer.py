import unittest
import asyncio
from fetchers.stock_analyzer import parse_ticker_from_text, analyze_stock_ticker, format_stock_report_card

class TestStockAnalyzer(unittest.TestCase):
    def test_parse_ticker_from_text(self):
        self.assertEqual(parse_ticker_from_text("/stock AAPL"), "AAPL")
        self.assertEqual(parse_ticker_from_text("$TSLA"), "TSLA")
        self.assertEqual(parse_ticker_from_text("NVDA"), "NVDA")
        self.assertEqual(parse_ticker_from_text("Tell me about Tesla"), "TSLA")
        self.assertEqual(parse_ticker_from_text("Microsoft news"), "MSFT")

    def test_analyze_stock_ticker(self):
        analysis = asyncio.run(analyze_stock_ticker("AAPL"))
        self.assertEqual(analysis["ticker"], "AAPL")
        self.assertIn("macro_context", analysis)
        self.assertIsInstance(analysis["selling_points"], list)
        self.assertIsInstance(analysis["risk_factors"], list)

    def test_format_stock_report_card(self):
        mock_analysis = {
            "ticker": "AAPL",
            "total_news_found": 5,
            "headlines": [{"title": "Apple Announces New AI Chip", "link": "https://example.com/aapl"}],
            "selling_points": [{"title": "Strong iPhone Sales Growth"}],
            "risk_factors": [{"title": "Supply Chain Component Delays"}],
            "general_news": [],
            "macro_context": "Lower Fed rates boost valuation."
        }
        card = format_stock_report_card(mock_analysis)
        self.assertIn("STOCK ANALYSIS REPORT: $AAPL", card)
        self.assertIn("KEY SELLING POINTS", card)
        self.assertIn("KEY RISKS", card)
        self.assertIn("Strong iPhone Sales Growth", card)
        self.assertIn("Supply Chain Component Delays", card)

if __name__ == "__main__":
    unittest.main()
