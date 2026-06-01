import sqlite3
import os
import threading

DB_PATH = os.environ.get("DB_PATH", "bot.db")

_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                first_name  TEXT,
                verified    INTEGER DEFAULT 0,
                gift_received INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER,
                PRIMARY KEY (referrer_id, referred_id)
            );

            CREATE TABLE IF NOT EXISTS join_requests (
                user_id INTEGER PRIMARY KEY
            );
        """)
        conn.commit()


# ─── USER ────────────────────────────────────────────────────────────────────

def register_user(user_id: int, first_name: str) -> bool:
    """Returns True if newly registered."""
    with _lock, get_conn() as conn:
        existing = conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (user_id, first_name) VALUES (?, ?)",
                (user_id, first_name)
            )
            conn.commit()
            return True
        return False


def is_verified(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT verified FROM users WHERE user_id=?", (user_id,)).fetchone()
        return bool(row and row["verified"])


def set_verified(user_id: int):
    with _lock, get_conn() as conn:
        conn.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
        conn.commit()


def has_received_gift(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT gift_received FROM users WHERE user_id=?", (user_id,)).fetchone()
        return bool(row and row["gift_received"])


def mark_gift_received(user_id: int):
    with _lock, get_conn() as conn:
        conn.execute("UPDATE users SET gift_received=1 WHERE user_id=?", (user_id,))
        conn.commit()


def get_user_count() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
        return row["c"] if row else 0


def get_all_user_ids() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
        return [r["user_id"] for r in rows]


# ─── REFERRALS ───────────────────────────────────────────────────────────────

def add_referral_if_needed(referrer_id: int, referred_id: int):
    """Record referral only if referred user is verified (called after verification)."""
    # We store it now; count only verified referrals
    with _lock, get_conn() as conn:
        existing = conn.execute(
            "SELECT 1 FROM referrals WHERE referrer_id=? AND referred_id=?",
            (referrer_id, referred_id)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                (referrer_id, referred_id)
            )
            conn.commit()


def get_referral_count(user_id: int) -> int:
    """Count verified users referred by this user."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) as c FROM referrals r
               JOIN users u ON r.referred_id = u.user_id
               WHERE r.referrer_id=? AND u.verified=1""",
            (user_id,)
        ).fetchone()
        return row["c"] if row else 0


def get_referrer(user_id: int):
    """Get who referred this user."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT referrer_id FROM referrals WHERE referred_id=?",
            (user_id,)
        ).fetchone()
        return row["referrer_id"] if row else None


# ─── JOIN REQUESTS ────────────────────────────────────────────────────────────

def record_join_request(user_id: int):
    with _lock, get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO join_requests (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()


def has_join_request(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM join_requests WHERE user_id=?", (user_id,)
        ).fetchone()
        return row is not None


# init on import
init_db()
