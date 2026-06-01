import sqlite3
import threading
import os

DB_PATH = os.getenv("DB_PATH", "bot.db")
lock = threading.Lock()


def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            verified INTEGER DEFAULT 0,
            gift INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS refs(
            referrer INTEGER,
            referred INTEGER UNIQUE
        );

        CREATE TABLE IF NOT EXISTS joins(
            user_id INTEGER PRIMARY KEY
        );
        """)


def add_user(uid, name):
    with lock, conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
            c.execute("INSERT INTO users VALUES(?,?,0,0)", (uid, name))


def verify(uid):
    with lock, conn() as c:
        c.execute("UPDATE users SET verified=1 WHERE user_id=?", (uid,))


def is_verified(uid):
    with conn() as c:
        r = c.execute("SELECT verified FROM users WHERE user_id=?", (uid,)).fetchone()
        return bool(r and r["verified"])


def add_ref(ref, uid):
    with lock, conn() as c:
        if not c.execute("SELECT 1 FROM refs WHERE referred=?", (uid,)).fetchone():
            c.execute("INSERT INTO refs VALUES(?,?)", (ref, uid))


def ref_count(uid):
    with conn() as c:
        r = c.execute("""
        SELECT COUNT(*) c FROM refs r
        JOIN users u ON r.referred=u.user_id
        WHERE r.referrer=? AND u.verified=1
        """, (uid,)).fetchone()
        return r["c"]


def add_join(uid):
    with lock, conn() as c:
        c.execute("INSERT OR IGNORE INTO joins VALUES(?)", (uid,))


def has_join(uid):
    with conn() as c:
        return c.execute("SELECT 1 FROM joins WHERE user_id=?", (uid,)).fetchone() is not None


def all_users():
    with conn() as c:
        return [i["user_id"] for i in c.execute("SELECT user_id FROM users")]
