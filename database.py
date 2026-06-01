import sqlite3
import threading
import os

DB_PATH = os.getenv("DB_PATH", "bot.db")

lock = threading.Lock()

def get_conn():
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
return conn

def init_db():
with get_conn() as conn:
conn.executescript("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
first_name TEXT,
verified INTEGER DEFAULT 0,
gift_received INTEGER DEFAULT 0,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```
    CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER UNIQUE
    );

    CREATE TABLE IF NOT EXISTS join_requests (
        user_id INTEGER PRIMARY KEY
    );
    """)
    conn.commit()
```

def register_user(user_id, first_name):
with lock:
with get_conn() as conn:
exists = conn.execute(
"SELECT user_id FROM users WHERE user_id=?",
(user_id,)
).fetchone()

```
        if not exists:
            conn.execute(
                "INSERT INTO users (user_id, first_name) VALUES (?, ?)",
                (user_id, first_name)
            )
            conn.commit()
            return True

        return False
```

def is_verified(user_id):
with get_conn() as conn:
row = conn.execute(
"SELECT verified FROM users WHERE user_id=?",
(user_id,)
).fetchone()

```
    return bool(row and row["verified"])
```

def set_verified(user_id):
with lock:
with get_conn() as conn:
conn.execute(
"UPDATE users SET verified=1 WHERE user_id=?",
(user_id,)
)
conn.commit()

def add_referral(referrer_id, referred_id):
with lock:
with get_conn() as conn:
exists = conn.execute(
"SELECT 1 FROM referrals WHERE referred_id=?",
(referred_id,)
).fetchone()

```
        if not exists:
            conn.execute(
                "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                (referrer_id, referred_id)
            )
            conn.commit()
```

def get_referrer(user_id):
with get_conn() as conn:
row = conn.execute(
"SELECT referrer_id FROM referrals WHERE referred_id=?",
(user_id,)
).fetchone()

```
    return row["referrer_id"] if row else None
```

def get_referral_count(user_id):
with get_conn() as conn:
row = conn.execute("""
SELECT COUNT(*) AS total
FROM referrals r
JOIN users u
ON r.referred_id = u.user_id
WHERE r.referrer_id=?
AND u.verified=1
""", (user_id,)).fetchone()

```
    return row["total"]
```

def record_join_request(user_id):
with lock:
with get_conn() as conn:
conn.execute(
"INSERT OR IGNORE INTO join_requests(user_id) VALUES(?)",
(user_id,)
)
conn.commit()

def has_join_request(user_id):
with get_conn() as conn:
row = conn.execute(
"SELECT 1 FROM join_requests WHERE user_id=?",
(user_id,)
).fetchone()

```
    return row is not None
```

def mark_gift_received(user_id):
with lock:
with get_conn() as conn:
conn.execute(
"UPDATE users SET gift_received=1 WHERE user_id=?",
(user_id,)
)
conn.commit()

def has_received_gift(user_id):
with get_conn() as conn:
row = conn.execute(
"SELECT gift_received FROM users WHERE user_id=?",
(user_id,)
).fetchone()

```
    return bool(row and row["gift_received"])
```

def get_user_count():
with get_conn() as conn:
row = conn.execute(
"SELECT COUNT(*) AS total FROM users"
).fetchone()

```
    return row["total"]
```

def get_all_user_ids():
with get_conn() as conn:
rows = conn.execute(
"SELECT user_id FROM users"
).fetchall()

```
    return [row["user_id"] for row in rows]
```

init_db()
