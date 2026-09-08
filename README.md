# 🏛️ Stock & Fed News Telegram Bot 🤝

A high-performance, asynchronous Python bot that monitors financial markets 24/7 and sends real-time alert cards to Telegram for **Federal Reserve announcements** and **Stock M&A / Acquisition press releases**.

---

## Key Features

- 🏛️ **Fed / FOMC Monitoring**: Scans official Federal Reserve press releases, rate hike/cut decisions, and Powell statements.
- 🤝 **M&A & Stock Acquisitions**: Monitors SEC EDGAR 8-K filings and financial RSS feeds for merger announcements, buyouts, and equity purchases.
- ⚡ **Low-Latency Async Engine**: Powered by `asyncio` & `aiohttp` to scan feeds concurrently every 10–15 seconds.
- 🚨 **Priority & Sentiment Scoring**: Categorizes alerts with HTML cards, ticker tags (`#AAPL`, `#NVDA`), and urgency badges.
- 💾 **SQLite Deduplication**: Prevents duplicate alert spamming across scanning loops.
- ☁️ **24/7 Cloud Ready**: Complete Docker container & deployment guides for Render.com, Railway, Fly.io, or VPS.

---

## Quick Start (Local Setup)

### 1. Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in:
- `TELEGRAM_BOT_TOKEN`: Token obtained from `@BotFather` on Telegram.
- `TELEGRAM_CHAT_ID`: Your personal user ID or Channel ID.
- `FINNHUB_API_KEY`: *(Optional)* Free API key from Finnhub.io for extra stock news feeds.

### 3. Run Bot Scanner
```bash
python main.py
```

---

## Project Structure

```
telegram-stock-news-bot/
├── bot/
│   ├── telegram_bot.py      # Interactive command handlers (/start, /latest, /status)
│   └── telegram_notifier.py # Formats HTML alert cards & dispatches via Telegram API
├── fetchers/
│   └── async_news_fetcher.py# Concurrent HTTP/RSS fetcher (Fed, SEC 8-K, Yahoo, Finnhub)
├── filters/
│   └── priority_filter.py   # Keyword matrix, ticker extraction & urgency scoring
├── config.py                # Environment & feed configuration settings
├── database.py              # SQLite cache & deduplication store
├── main.py                  # Async application entrypoint
├── Dockerfile               # 24/7 Cloud deployment container specification
├── docker-compose.yml       # Docker service definition
├── DEPLOYMENT.md            # Step-by-step 24/7 cloud hosting guide
└── requirements.txt         # Python dependencies
```

---

## 24/7 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on hosting on **Render.com** (Free), **Railway**, or **VPS**.
