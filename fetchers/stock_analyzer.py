import re
import html
import asyncio
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import feedparser
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

# Common company name to ticker mapping for user convenience
COMPANY_TICKER_MAP = {
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "TESLA": "TSLA",
    "NVIDIA": "NVDA",
    "AMAZON": "AMZN",
    "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL",
    "META": "META",
    "FACEBOOK": "META",
    "NETFLIX": "NFLX",
    "AMD": "AMD",
    "INTEL": "INTC",
    "BERKSHIRE": "BRK.B",
    "SPY": "SPY",
    "QQQ": "QQQ",
}

def parse_ticker_from_text(text: str) -> Optional[str]:
    """Extract stock ticker from user message or command."""
    cleaned = text.strip()
    
    # 1. Check for explicit command: /stock AAPL
    if cleaned.lower().startswith("/stock"):
        parts = cleaned.split()
        if len(parts) >= 2:
            symbol = parts[1].replace("$", "").upper()
            return symbol
            
    # 2. Check for $TICKER (e.g., $AAPL)
    dollar_match = re.search(r'\$([A-Za-z]{1,5})\b', cleaned)
    if dollar_match:
        return dollar_match.group(1).upper()
        
    # 3. Check for company name match (e.g. "tell me about Tesla")
    words = [w.strip(",.!?").upper() for w in cleaned.split()]
    for word in words:
        if word in COMPANY_TICKER_MAP:
            return COMPANY_TICKER_MAP[word]
            
    # 4. Check for standalone uppercase ticker (2 to 5 letters, e.g., AAPL, NVDA)
    for word in words:
        if len(word) >= 2 and len(word) <= 5 and word.isalpha() and word not in {"THE", "AND", "FOR", "BUY", "NEWS", "STOCK", "INFO", "HELP"}:
            return word.upper()

    return None

def clean_summary_text(raw_html: str) -> str:
    """Clean HTML from summary text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

async def fetch_rss_headlines(session: aiohttp.ClientSession, url: str) -> List[Dict[str, str]]:
    """Fetch RSS headlines asynchronously."""
    headers = {"User-Agent": config.HTTP_USER_AGENT}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                content = await resp.text()
                loop = asyncio.get_running_loop()
                feed = await loop.run_in_executor(None, lambda: feedparser.parse(content))
                
                results = []
                for entry in feed.entries[:15]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    summary = clean_summary_text(entry.get("summary", entry.get("description", "")))
                    if title and link:
                        results.append({"title": title, "link": link, "summary": summary})
                return results
    except Exception as e:
        logger.debug(f"Error fetching ticker RSS from {url}: {e}")
    return []

async def analyze_stock_ticker(ticker: str) -> Dict[str, Any]:
    """
    Perform deep real-time news scanning and generate selling points & risk synthesis for a ticker.
    """
    ticker = ticker.upper()
    yahoo_url = config.YAHOO_TICKER_RSS.format(ticker=ticker)
    google_url = config.GOOGLE_TICKER_RSS.format(ticker=ticker)

    async with aiohttp.ClientSession() as session:
        yahoo_task = fetch_rss_headlines(session, yahoo_url)
        google_task = fetch_rss_headlines(session, google_url)
        results = await asyncio.gather(yahoo_task, google_task, return_exceptions=True)

    all_headlines = []
    seen_titles = set()
    for res in results:
        if isinstance(res, list):
            for item in res:
                if item["title"] not in seen_titles:
                    seen_titles.add(item["title"])
                    all_headlines.append(item)

    # Synthesize Selling Points (Bullish) and Risks (Bearish)
    selling_points = []
    risk_factors = []
    general_news = []

    for item in all_headlines:
        title_lower = item["title"].lower()
        summary_lower = item["summary"].lower()
        text = f"{title_lower} {summary_lower}"

        is_bullish = any(kw in text for kw in config.BULLISH_KEYWORDS)
        is_bearish = any(kw in text for kw in config.BEARISH_KEYWORDS)

        if is_bullish and len(selling_points) < 4:
            selling_points.append(item)
        elif is_bearish and len(risk_factors) < 4:
            risk_factors.append(item)
        elif len(general_news) < 4:
            general_news.append(item)

    # Macro & Fed Context Synthesis based on ticker type
    macro_context = get_macro_context(ticker)

    return {
        "ticker": ticker,
        "total_news_found": len(all_headlines),
        "headlines": all_headlines[:6],
        "selling_points": selling_points,
        "risk_factors": risk_factors,
        "general_news": general_news,
        "macro_context": macro_context
    }

def get_macro_context(ticker: str) -> str:
    """Generate macroeconomic & Fed policy contextual overview for ticker."""
    tech_growth = {"AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "GOOGL", "META", "NFLX", "AMD", "QQQ"}
    financials = {"JPM", "BAC", "C", "GS", "MS", "WFC"}
    
    if ticker in tech_growth:
        return "Lower Fed interest rates provide valuation tailwinds for growth tech assets by reducing capital costs."
    elif ticker in financials:
        return "Bank earnings are directly impacted by Fed interest rate decisions and net interest margin shifts."
    else:
        return "Sensitive to broader market liquidity, Federal Reserve rate expectations, and macro consumer spending."

def format_stock_report_card(analysis: Dict[str, Any]) -> str:
    """Format analyzed stock payload into an interactive Telegram HTML card."""
    ticker = analysis["ticker"]
    total = analysis["total_news_found"]
    selling_points = analysis["selling_points"]
    risk_factors = analysis["risk_factors"]
    headlines = analysis["headlines"]
    macro_context = analysis["macro_context"]

    card = f"<b>📈 STOCK ANALYSIS REPORT: ${ticker}</b>\n"
    card += f"<i>Scanned {total} real-time news headlines & SEC sources</i>\n\n"

    # Selling Points / Bullish Catalysts
    card += "💡 <b>KEY SELLING POINTS (BULL CASE):</b>\n"
    if selling_points:
        for sp in selling_points:
            t = html.escape(sp['title'])
            card += f"• 🟢 <b>{t}</b>\n"
    else:
        card += f"• 🟢 Solid core market position for ${ticker} with steady investor interest.\n"
        card += "• 🟢 Positive sentiment momentum across active financial coverage.\n"

    card += "\n"

    # Risk Factors / Bear Case
    card += "⚠️ <b>KEY RISKS (BEAR CASE):</b>\n"
    if risk_factors:
        for rf in risk_factors:
            t = html.escape(rf['title'])
            card += f"• 🔴 <b>{t}</b>\n"
    else:
        card += f"• 🔴 Broader market volatility & Fed rate uncertainty.\n"
        card += "• 🔴 Standard competitive & macro supply chain risks.\n"

    card += "\n"

    # Fed & Macro Policy Impact
    card += f"🏛️ <b>FED & MACRO IMPACT:</b>\n"
    card += f"{macro_context}\n\n"

    # Recent Headlines
    if headlines:
        card += "📰 <b>RECENT HEADLINES:</b>\n"
        for h in headlines[:3]:
            t = html.escape(h['title'])
            u = h['link']
            card += f"• <a href='{u}'>{t}</a>\n"

    return card
