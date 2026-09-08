import re
from typing import Dict, Any, List, Tuple, Optional
import config

# Regular expression to extract potential stock tickers (e.g., $AAPL, $TSLA, or uppercase 2-5 letter symbols)
TICKER_REGEX = re.compile(r'\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b')

# Common non-ticker words to exclude when regex matching
COMMON_WORDS_EXCLUDE = {
    "FED", "USA", "SEC", "CEO", "CFO", "IPO", "EST", "EDT", "USD", "EUR", "GDP",
    "CPI", "PCE", "FOMC", "NOTE", "NEWS", "NYSE", "AMEX", "WALL", "BANK", "BOND",
    "THE", "AND", "FOR", "BUY", "NEW", "RAW", "WAR", "OIL", "GAS", "TAX", "APP"
}

def analyze_article(title: str, summary: str = "") -> Dict[str, Any]:
    """
    Analyze title and summary text to extract category, urgency, detected tickers, and relevance.
    """
    combined_text = f"{title} {summary}".lower()
    
    # Priority keyword matching
    is_fed = any(kw in combined_text for kw in config.FED_KEYWORDS)
    is_ma = any(kw in combined_text for kw in config.MA_KEYWORDS)
    is_earnings = any(kw in combined_text for kw in config.EARNINGS_KEYWORDS)

    # Determine primary category and urgency
    category = "OTHER"
    urgency = "NORMAL"
    badge = "📰 MARKET NEWS"

    if is_fed and is_ma:
        category = "FED & MA"
        urgency = "HIGH"
        badge = "🚨 HIGH IMPACT - FED & M&A"
    elif is_fed:
        category = "FED"
        urgency = "HIGH"
        badge = "🏛️ FED ANNOUNCEMENT"
    elif is_ma:
        category = "M&A"
        urgency = "HIGH"
        badge = "🤝 MERGER & ACQUISITION"
    elif is_earnings:
        category = "EARNINGS"
        urgency = "MEDIUM"
        badge = "📊 CORPORATE EARNINGS"

    # Extract ticker candidates
    tickers = extract_tickers(f"{title} {summary}")

    is_relevant = (is_fed or is_ma or is_earnings)

    return {
        "category": category,
        "urgency": urgency,
        "badge": badge,
        "is_relevant": is_relevant,
        "tickers": tickers
    }

def extract_tickers(text: str) -> List[str]:
    """Extract stock tickers formatted with $ prefix."""
    found = set()
    
    # Direct $TICKER matches first
    dollar_matches = re.findall(r'\$([A-Z]{1,5})\b', text)
    for m in dollar_matches:
        if m.upper() not in COMMON_WORDS_EXCLUDE:
            found.add(f"${m.upper()}")
            
    # Uppercase symbol matches
    plain_matches = re.findall(r'\b([A-Z]{2,5})\b', text)
    for m in plain_matches:
        # Require uppercase in raw text
        if m in COMMON_WORDS_EXCLUDE:
            continue
        if m.isupper() and len(m) >= 2:
            # Simple heuristic for potential tickers
            if f"${m}" in found or len(m) <= 4:
                found.add(f"${m}")
                
    return sorted(list(found))[:5] # Limit to top 5 tickers
