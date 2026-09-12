import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "reviews.db")


def get_connection():
    """Ensure data/ directory exists and return SQLite connection."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize SQLite database table in data/reviews.db."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            proposal_id TEXT PRIMARY KEY,
            facility_name TEXT,
            action TEXT,
            details TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()