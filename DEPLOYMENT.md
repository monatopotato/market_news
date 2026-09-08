# 24/7 Cloud Deployment Guide (Run Without Keeping Computer On)

This guide shows you how to deploy your **Stock & Fed News Telegram Bot** to free or ultra-low-cost cloud servers so it runs 24/7 automatically.

---

## Option 1: Render.com (Recommended Free / Easy Setup)

Render offers free hosting tier for background services.

### Steps:
1. Push your project repository to GitHub / GitLab.
2. Sign up at [Render.com](https://render.com).
3. Click **New +** -> Select **Background Worker**.
4. Connect your GitHub repository.
5. Set build & runtime parameters:
   - **Environment**: `Python 3` (or `Docker`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
6. Scroll to **Environment Variables** and add:
   - `TELEGRAM_BOT_TOKEN` = `your_token_from_botfather`
   - `TELEGRAM_CHAT_ID` = `your_chat_id`
   - `FINNHUB_API_KEY` = `(optional)`
   - `POLL_INTERVAL_SECONDS` = `15`
7. Click **Create Background Worker**. Render will build and launch your bot 24/7!

---

## Option 2: Railway.app (Ultra Fast 1-Click Deploy)

1. Sign up at [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub Repo**.
3. Railway automatically detects the `Dockerfile` and `Procfile`.
4. Go to **Variables** tab and paste your `.env` variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
5. Click **Deploy**. The bot will immediately begin scanning 24/7.

---

## Option 3: VPS Server (DigitalOcean, Hetzner, AWS Lightsail - \$4-5/mo)

If you have a Linux VPS:

```bash
# 1. Clone repository onto server
git clone https://github.com/yourusername/telegram-stock-news-bot.git
cd telegram-stock-news-bot

# 2. Create .env file
cp .env.example .env
nano .env  # Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

# 3. Launch container with Docker Compose
docker-compose up -d --build

# Check live logs
docker-compose logs -f
```

---

## How to Get Your Telegram Bot Token & Chat ID

### Step 1: Get Bot Token
1. Open Telegram and search for `@BotFather`.
2. Send command: `/newbot`.
3. Give your bot a name (e.g. `MyStockNewsBot`) and username ending in `bot`.
4. Copy the HTTP API token provided by BotFather (e.g. `789101112:AAH...`).

### Step 2: Get Your Chat ID
1. Search for `@userinfobot` or `@raw_data_bot` on Telegram and click **Start**.
2. Copy your `Id` number (e.g., `123456789`).
3. For Telegram Channels: Add your bot as an admin to the channel, and use the Channel `@username` (e.g. `@my_stock_channel`) or ID.
