import re
from typing import Dict, Any, List, Set, Tuple, Optional
import config

# Regular expression to extract potential stock tickers (e.g., $AAPL, $TSLA, or uppercase 2-5 letter symbols)
TICKER_REGEX = re.compile(r'\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b')

# S&P 500 Major Companies & Tickers Focus Set
SP500_KEYWORDS = {
    # Tickers
    "aapl", "msft", "nvda", "amzn", "googl", "goog", "meta", "tsla", "brk.b", "brk.a",
    "lly", "jpm", "avgo", "wmt", "v", "xom", "unh", "ma", "pg", "jnj", "hd", "cost",
    "abbv", "bac", "nflx", "cvx", "ko", "mrk", "crm", "amd", "pep", "adbe", "tmo",
    "mcd", "csco", "acn", "abt", "dis", "qcom", "wfc", "ge", "cat", "txn", "vz",
    "orcl", "intu", "cmcsa", "ibm", "amat", "amgn", "pfe", "hon", "ms", "uber",
    "now", "gs", "isrg", "rtx", "unp", "low", "spy", "qqq", "s&p", "sp500", "s&p 500",
    # Major Company Names
    "apple", "microsoft", "nvidia", "amazon", "google", "alphabet", "facebook",
    "tesla", "berkshire", "jpmorgan", "walmart", "visa", "exxon", "unitedhealth",
    "mastercard", "procter & gamble", "johnson & johnson", "home depot", "costco",
    "bank of america", "netflix", "chevron", "coca-cola", "coca cola", "pepsi",
    "salesforce", "mcdonald", "disney", "qualcomm", "wells fargo", "general electric",
    "caterpillar", "verizon", "oracle", "boeing", "goldman sachs", "morgan stanley"
}

# Common non-ticker words to exclude when regex matching
COMMON_WORDS_EXCLUDE = {
    "FED", "USA", "SEC", "CEO", "CFO", "IPO", "EST", "EDT", "USD", "EUR", "GDP",
    "CPI", "PCE", "FOMC", "NOTE", "NEWS", "NYSE", "AMEX", "WALL", "BANK", "BOND",
    "THE", "AND", "FOR", "BUY", "NEW", "RAW", "WAR", "OIL", "GAS", "TAX", "APP"
}

def is_sp500_related(text: str) -> bool:
    """Check if text is explicitly related to an S&P 500 company or Fed policy."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in SP500_KEYWORDS)

def analyze_article(title: str, summary: str = "") -> Dict[str, Any]:
    """
    Analyze title and summary text to extract category, urgency, detected tickers, and relevance.
    Strictly filters for S&P 500 companies & Federal Reserve announcements.
    """
    combined_text = f"{title} {summary}".lower()
    
    # Priority keyword matching
    is_fed = any(kw in combined_text for kw in config.FED_KEYWORDS)
    is_ma = any(kw in combined_text for kw in config.MA_KEYWORDS)
    is_earnings = any(kw in combined_text for kw in config.EARNINGS_KEYWORDS)
    is_sp500 = is_sp500_related(combined_text)

    # Relevancy Rule: MUST be Federal Reserve OR S&P 500 related!
    is_relevant = is_fed or (is_sp500 and (is_ma or is_earnings))

    # Determine primary category and urgency
    category = "OTHER"
    urgency = "NORMAL"
    badge = "📰 S&P 500 MARKET NEWS"

    if is_fed and is_ma:
        category = "FED & MA"
        urgency = "HIGH"
        badge = "🚨 HIGH IMPACT - FED & S&P 500 M&A"
    elif is_fed:
        category = "FED"
        urgency = "HIGH"
        badge = "🏛️ FED ANNOUNCEMENT"
    elif is_ma and is_sp500:
        category = "M&A"
        urgency = "HIGH"
        badge = "🤝 S&P 500 MERGER & ACQUISITION"
    elif is_earnings and is_sp500:
        category = "EARNINGS"
        urgency = "MEDIUM"
        badge = "📊 S&P 500 CORPORATE EARNINGS"

    # Extract ticker candidates
    tickers = extract_tickers(f"{title} {summary}")

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
        if m in COMMON_WORDS_EXCLUDE:
            continue
        if m.isupper() and len(m) >= 2:
            if f"${m}" in found or len(m) <= 4:
                found.add(f"${m}")
                
    return sorted(list(found))[:5] # Limit to top 5 tickers
