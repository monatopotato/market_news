import asyncio
import logging
from typing import List, Dict, Any
import aiohttp
import feedparser
from bs4 import BeautifulSoup

import config
from database import generate_article_id, is_article_processed
from filters.priority_filter import analyze_article

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": config.HTTP_USER_AGENT,
    "Accept": "application/atom+xml,application/xml,text/xml,application/json,*/*"
}

async def fetch_url(session: aiohttp.ClientSession, url: str, is_json: bool = False) -> Any:
    """Fetch URL content asynchronously with error handling."""
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                if is_json:
                    return await response.json()
                return await response.text()
            else:
                logger.warning(f"HTTP {response.status} fetching {url}")
                return None
    except Exception as e:
        logger.debug(f"Error fetching {url}: {e}")
        return None

def clean_html(raw_html: str) -> str:
    """Strip HTML tags from RSS summary strings."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

async def parse_rss_feed(session: aiohttp.ClientSession, url: str, source_name: str) -> List[Dict[str, Any]]:
    """Parse RSS feed XML asynchronously."""
    content = await fetch_url(session, url)
    if not content:
        return []

    # feedparser runs synchronously, so run in executor to avoid blocking async loop
    loop = asyncio.get_running_loop()
    feed = await loop.run_in_executor(None, lambda: feedparser.parse(content))
    
    articles = []
    for entry in feed.entries[:25]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = clean_html(entry.get("summary", entry.get("description", "")))
        published = entry.get("published", entry.get("updated", ""))

        if not title or not link:
            continue

        article_id = generate_article_id(link, title)
        if is_article_processed(article_id):
            continue

        analysis = analyze_article(title, summary)
        if not analysis["is_relevant"]:
            continue

        articles.append({
            "id": article_id,
            "title": title,
            "url": link,
            "summary": summary[:300],
            "source": source_name,
            "category": analysis["category"],
            "urgency": analysis["urgency"],
            "badge": analysis["badge"],
            "tickers": analysis["tickers"],
            "published_at": published
        })
        
    return articles

async def fetch_finnhub_news(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Fetch real-time financial market news from Finnhub API if key provided."""
    if not config.FINNHUB_API_KEY:
        return []

    url = f"https://finnhub.io/api/v1/news?category=general&token={config.FINNHUB_API_KEY}"
    data = await fetch_url(session, url, is_json=True)
    if not data or not isinstance(data, list):
        return []

    articles = []
    for item in data[:20]:
        title = item.get("headline", "").strip()
        link = item.get("url", "").strip()
        summary = item.get("summary", "").strip()
        published = str(item.get("datetime", ""))
        source = f"Finnhub ({item.get('source', 'General')})"

        if not title or not link:
            continue

        article_id = generate_article_id(link, title)
        if is_article_processed(article_id):
            continue

        analysis = analyze_article(title, summary)
        if not analysis["is_relevant"]:
            continue

        articles.append({
            "id": article_id,
            "title": title,
            "url": link,
            "summary": summary[:300],
            "source": source,
            "category": analysis["category"],
            "urgency": analysis["urgency"],
            "badge": analysis["badge"],
            "tickers": analysis["tickers"],
            "published_at": published
        })

    return articles

async def fetch_all_sources() -> List[Dict[str, Any]]:
    """Run all async fetchers concurrently and return combined unique new articles."""
    async with aiohttp.ClientSession() as session:
        tasks = [
            parse_rss_feed(session, config.FED_PRESS_RELEASES_RSS, "Federal Reserve"),
            parse_rss_feed(session, config.SEC_EDGAR_8K_RSS, "SEC EDGAR 8-K"),
            parse_rss_feed(session, config.GOOGLE_NEWS_FED_RSS, "Google News (Fed)"),
            parse_rss_feed(session, config.GOOGLE_NEWS_MA_RSS, "Google News (M&A)"),
            parse_rss_feed(session, config.YAHOO_FINANCE_RSS, "Yahoo Finance"),
            fetch_finnhub_news(session),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_articles: List[Dict[str, Any]] = []
    seen_ids = set()

    for res in results:
        if isinstance(res, Exception):
            logger.error(f"Fetcher task error: {res}")
            continue
        for article in res:
            if article["id"] not in seen_ids:
                seen_ids.add(article["id"])
                combined_articles.append(article)

    # Sort high urgency first
    combined_articles.sort(key=lambda x: 0 if x["urgency"] == "HIGH" else 1)
    return combined_articles
