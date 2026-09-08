import logging
import html
from typing import Dict, Any, Optional
import aiohttp
import config
from database import mark_article_processed

logger = logging.getLogger(__name__)

def format_alert_card(article: Dict[str, Any]) -> str:
    """Format an article payload into a Telegram HTML alert message."""
    badge = article.get("badge", "📰 MARKET NEWS")
    title = html.escape(article.get("title", ""))
    summary = html.escape(article.get("summary", ""))
    url = article.get("url", "")
    source = html.escape(article.get("source", "Unknown"))
    published = html.escape(article.get("published_at", ""))
    tickers = article.get("tickers", [])

    ticker_str = ""
    if tickers:
        formatted_tickers = " ".join([f"#{t.replace('$', '')}" for t in tickers])
        ticker_str = f"<b>Tickers:</b> {formatted_tickers}\n"

    summary_str = f"<b>Summary:</b> {summary}\n\n" if summary else "\n"
    published_str = f"<b>Time:</b> {published}\n" if published else ""

    card = (
        f"<b>{badge}</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"{ticker_str}"
        f"{summary_str}"
        f"<b>Source:</b> {source}\n"
        f"{published_str}"
        f"🔗 <a href='{url}'>Read Full Announcement</a>"
    )
    return card

async def send_telegram_alert(session: aiohttp.ClientSession, article: Dict[str, Any]) -> bool:
    """Send Telegram message via Telegram Bot API asynchronously."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.info(f"[MOCK TELEGRAM ALERT]: {article['badge']} | {article['title']}")
        # Mark as processed in mock mode so we don't re-log repeatedly
        mark_article_processed(
            article["id"], article["title"], article["url"],
            article["source"], article.get("category", "OTHER"), article.get("published_at")
        )
        return True

    api_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    text = format_alert_card(article)

    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                mark_article_processed(
                    article["id"], article["title"], article["url"],
                    article["source"], article.get("category", "OTHER"), article.get("published_at")
                )
                logger.info(f"Telegram alert sent: {article['title']}")
                return True
            else:
                resp_text = await response.text()
                logger.error(f"Telegram API Error {response.status}: {resp_text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False

async def send_digest_summary(session: aiohttp.ClientSession) -> bool:
    """Send periodic 2-hour market news digest summary to Telegram."""
    from database import get_recent_articles
    articles = get_recent_articles(limit=6)
    
    if not articles:
        text = "<b>📰 2-HOUR MARKET NEWS DIGEST</b>\n\n<i>No major market-moving updates in the last scan window. Scanner active 24/7.</i>"
    else:
        text = "<b>📰 2-HOUR MARKET NEWS DIGEST</b>\n\n"
        for idx, a in enumerate(articles, 1):
            cat_emoji = "🏛️" if "FED" in a["category"] else "🤝" if "M&A" in a["category"] else "📊"
            title = html.escape(a["title"])
            url = a["url"]
            source = html.escape(a["source"])
            text += f"{idx}. {cat_emoji} <b><a href='{url}'>{title}</a></b>\n   <i>Source: {source}</i>\n\n"

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.info(f"[MOCK DIGEST SENT]:\n{text}")
        return True

    api_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                logger.info("2-Hour Market Digest sent to Telegram.")
                return True
            else:
                resp_text = await response.text()
                logger.error(f"Telegram API Digest Error {response.status}: {resp_text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram digest: {e}")
        return False

