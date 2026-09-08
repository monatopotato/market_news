import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Optional API Keys
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Scanner Settings
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "15"))
PERIODIC_DIGEST_INTERVAL_SECONDS = int(os.getenv("PERIODIC_DIGEST_INTERVAL_SECONDS", "7200")) # Default 2 hours (7200 sec)
DB_PATH = os.getenv("DB_PATH", "news_cache.db")

# User Agent for HTTP requests (SEC EDGAR requires a specific format: User-Agent: Sample Company Name AdminContact@<sample company domain>.com)
HTTP_USER_AGENT = os.getenv(
    "HTTP_USER_AGENT",
    "StockNewsTelegramBot/1.0 (contact: trader@example.com)"
)

# RSS Feed URLs
FED_PRESS_RELEASES_RSS = "https://www.federalreserve.gov/feeds/press_all.xml"
SEC_EDGAR_8K_RSS = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&datea=&dateb=&owner=include&count=40&output=atom"
YAHOO_FINANCE_RSS = "https://finance.yahoo.com/news/rssindex"

# Google News RSS Queries for targeted rapid indexing
GOOGLE_NEWS_FED_RSS = "https://news.google.com/rss/search?q=Federal+Reserve+interest+rate+OR+FOMC+OR+Powell&hl=en-US&gl=US&ceid=US:en"
GOOGLE_NEWS_MA_RSS = "https://news.google.com/rss/search?q=acquired+OR+merger+OR+acquisition+OR+buyout+when:1d&hl=en-US&gl=US&ceid=US:en"

# Keyword Categories
FED_KEYWORDS = [
    "federal reserve", "fomc", "powell", "jerome powell",
    "interest rate", "rate hike", "rate cut", "basis points", "bps",
    "monetary policy", "inflation", "cpi", "pce", "fed decision",
    "discount rate", "treasury yield", "quantitative easing", "tightening"
]

MA_KEYWORDS = [
    "acquired", "acquisition", "merger", "buyout", "takeover",
    "to buy", "agrees to buy", "definitive agreement", "stake in",
    "buying equity", "tender offer", "spinoff", "merging with"
]

EARNINGS_KEYWORDS = [
    "earnings", "quarterly results", "revenue missed", "revenue beat",
    "guidance", "eps", "net income", "fiscal quarter"
]

# Ticker Lookup RSS Templates
YAHOO_TICKER_RSS = "https://finance.yahoo.com/rss/headline?s={ticker}"
GOOGLE_TICKER_RSS = "https://news.google.com/rss/search?q={ticker}+stock+OR+{ticker}+earnings+when:7d&hl=en-US&gl=US&ceid=US:en"

# Bullish / Selling Point Keywords
BULLISH_KEYWORDS = [
    "beat", "growth", "upgrade", "buy", "record", "surge", "rally",
    "partnership", "outperform", "profit", "expansion", "dividend",
    "approval", "patent", "innovation", "strong demand", "bullish"
]

# Bearish / Risk Keywords
BEARISH_KEYWORDS = [
    "miss", "drop", "fall", "downgrade", "cut", "lawsuit", "investigation",
    "loss", "decline", "warning", "risk", "delay", "probe", "headwind",
    "debt", "layoffs", "bearish"
]

