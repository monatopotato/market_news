import sqlite3
import hashlib
from typing import List, Dict, Optional, Tuple
from config import DB_PATH

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db(db_path: str = DB_PATH) -> None:
    """Initialize the SQLite database schema if not already present."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                published_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);")
        conn.commit()

def generate_article_id(url: str, title: str) -> str:
    """Generate a deterministic unique ID based on article URL or title."""
    raw = f"{url.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def is_article_processed(article_id: str, db_path: str = DB_PATH) -> bool:
    """Check if an article has already been processed and alerted."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM articles WHERE id = ?", (article_id,))
        return cursor.fetchone() is not None

def mark_article_processed(
    article_id: str,
    title: str,
    url: str,
    source: str,
    category: str,
    published_at: Optional[str] = None,
    db_path: str = DB_PATH
) -> None:
    """Insert article record into database to prevent duplicate alerts."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO articles (id, title, url, source, category, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (article_id, title, url, source, category, published_at or ""))
        conn.commit()

def get_recent_articles(limit: int = 10, db_path: str = DB_PATH) -> List[Dict[str, str]]:
    """Retrieve the most recent alerted articles."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, url, source, category, published_at, created_at
            FROM articles
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        
        return [
            {
                "id": r[0],
                "title": r[1],
                "url": r[2],
                "source": r[3],
                "category": r[4],
                "published_at": r[5],
                "created_at": r[6]
            }
            for r in rows
        ]

def count_recent_alerts_last_hour(db_path: str = DB_PATH) -> int:
    """Count how many instant alerts were sent in the last 60 minutes."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM articles
            WHERE datetime(created_at) >= datetime('now', '-1 hour')
        """)
        row = cursor.fetchone()
        return row[0] if row else 0
