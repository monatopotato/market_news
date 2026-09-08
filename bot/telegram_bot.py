import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import config
from database import get_recent_articles
from fetchers.stock_analyzer import parse_ticker_from_text, analyze_stock_ticker, format_stock_report_card

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message upon /start command."""
    welcome_text = (
        "🤖 <b>Stock & Fed News Alert Bot Active!</b>\n\n"
        "I monitor financial markets 24/7 for instant high-impact news:\n"
        "• 🏛️ <b>Federal Reserve / FOMC</b> interest rate decisions\n"
        "• 🤝 <b>Mergers & Acquisitions</b> press releases\n"
        "• 📊 <b>SEC 8-K filings & Corporate announcements</b>\n\n"
        "<b>💡 Interactive Stock Analyzer:</b>\n"
        "Text me any stock ticker (e.g. <code>$AAPL</code>, <code>TSLA</code>, or <code>/stock NVDA</code>) "
        "and I will reply with key selling points, risk factors, and live news!\n\n"
        "<b>Available Commands:</b>\n"
        "/stock &lt;ticker&gt; - Analyze stock & selling points\n"
        "/latest - View recent alerts\n"
        "/status - Check bot & scanner status\n"
        "/ping - Test bot responsiveness\n"
        "/help - Display usage instructions\n"
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="HTML")

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyze a specific stock symbol requested by user via /stock <symbol>."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    ticker = parse_ticker_from_text(text)
    
    if not ticker:
        await update.message.reply_text(
            "❓ Please specify a valid ticker. Example: <code>/stock AAPL</code> or <code>$TSLA</code>",
            parse_mode="HTML"
        )
        return

    await process_stock_query(update, ticker)

async def handle_text_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically detect stock tickers sent in normal chat messages."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    ticker = parse_ticker_from_text(text)
    if ticker:
        await process_stock_query(update, ticker)

async def process_stock_query(update: Update, ticker: str) -> None:
    """Perform stock analysis and send card reply."""
    if not update.message:
        return

    status_msg = await update.message.reply_text(
        f"🔍 <i>Analyzing ${ticker}... Searching live news & selling points</i>",
        parse_mode="HTML"
    )

    try:
        analysis = await analyze_stock_ticker(ticker)
        card = format_stock_report_card(analysis)
        
        # Delete temporary scanning status message
        try:
            await status_msg.delete()
        except Exception:
            pass

        await update.message.reply_text(card, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error processing stock query for ${ticker}: {e}")
        await update.message.reply_text(
            f"❌ Unable to fetch report for ${ticker} at this time. Please try again.",
            parse_mode="HTML"
        )

async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return top 5 recent announcements saved in database."""
    articles = get_recent_articles(limit=5)
    if not articles:
        if update.message:
            await update.message.reply_text("ℹ️ No announcements saved yet. Scanner is searching...")
        return

    response = "<b>📰 Recent High-Impact Announcements:</b>\n\n"
    for idx, a in enumerate(articles, 1):
        cat_emoji = "🏛️" if "FED" in a["category"] else "🤝" if "M&A" in a["category"] else "📰"
        response += f"{idx}. {cat_emoji} <b>{a['title']}</b>\n"
        response += f"   <i>Source: {a['source']}</i>\n"
        response += f"   🔗 <a href='{a['url']}'>Link</a>\n\n"

    if update.message:
        await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report scanner loop status and stored article metrics."""
    articles = get_recent_articles(limit=100)
    status_text = (
        "🟢 <b>Bot Status: RUNNING</b>\n\n"
        f"⏱️ <b>Scan Frequency:</b> Every {config.POLL_INTERVAL_SECONDS} seconds\n"
        f"📦 <b>Total Stored Articles:</b> {len(articles)}\n"
        f"⚡ <b>Finnhub API Enabled:</b> {'Yes' if config.FINNHUB_API_KEY else 'No (Using standard RSS/EDGAR)'}\n"
    )
    if update.message:
        await update.message.reply_text(status_text, parse_mode="HTML")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping response test."""
    if update.message:
        await update.message.reply_text("🏓 <b>Pong!</b> News bot is online and scanning.", parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information."""
    help_text = (
        "<b>📖 Bot Usage Guide</b>\n\n"
        "This bot scans news feeds every 10–15 seconds asynchronously. "
        "When market-moving Fed rate updates or M&A stock news are discovered, "
        "an alert card will automatically be pushed to this chat.\n\n"
        "<b>💡 Interactive Stock Analyzer:</b>\n"
        "Text me any stock ticker (e.g. <code>$AAPL</code>, <code>TSLA</code>, or <code>/stock NVDA</code>) "
        "and I will reply with key selling points, risk factors, and live news!\n\n"
        "<b>Commands:</b>\n"
        "/stock &lt;ticker&gt; - Analyze stock selling points & news\n"
        "/latest - Get top 5 recent news alerts\n"
        "/status - Check scanner statistics\n"
        "/ping - Latency test\n"
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="HTML")

def build_telegram_app() -> Application:
    """Construct telegram application instance with handlers."""
    if not config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stock", stock_command))
    app.add_handler(CommandHandler("latest", latest_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_query))

    return app
