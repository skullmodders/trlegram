"""
Advanced IP Verification Server for Telegram Bot
Fixed, production-ready version with full bot integration.
"""

from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os
import logging
import hashlib
import hmac
import time
import requests
from datetime import datetime, timezone
from functools import wraps

# ──────────────────────────────────────────────
# App & Logging Setup
# ──────────────────────────────────────────────
app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
DB_PATH      = os.environ.get("DB_PATH", "/data/bot_database.db")
BOT_TOKEN    = os.environ.get("BOT_TOKEN", "8346441928:AAFf6e7qpc8ZnF4mvLk8nXNxvIXT68AH_to")
ADMIN_IDS    = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
SECRET_KEY   = os.environ.get("SECRET_KEY", hashlib.sha256(BOT_TOKEN.encode()).hexdigest())

# ──────────────────────────────────────────────
# HTML Templates
# ──────────────────────────────────────────────
_BASE_STYLE = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:      #060b14;
    --panel:   #0d1829;
    --border:  rgba(56, 189, 248, 0.15);
    --green:   #22d3a5;
    --red:     #f43f5e;
    --blue:    #38bdf8;
    --text:    #e2e8f0;
    --muted:   #94a3b8;
    --radius:  20px;
  }

  body {
    min-height: 100vh;
    background: var(--bg);
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    background-image:
      radial-gradient(ellipse 80% 60% at 50% -10%, rgba(56,189,248,0.08) 0%, transparent 70%);
  }

  .card {
    width: 100%; max-width: 440px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 40px 32px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(56,189,248,0.06);
    animation: slideUp 0.45s cubic-bezier(0.22,1,0.36,1) both;
  }

  @keyframes slideUp {
    from { opacity:0; transform: translateY(24px); }
    to   { opacity:1; transform: translateY(0); }
  }

  .card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent-line);
  }

  .icon {
    font-size: 52px; display: block; margin-bottom: 18px;
    animation: popIn 0.5s 0.2s cubic-bezier(0.34,1.56,0.64,1) both;
  }
  @keyframes popIn {
    from { opacity:0; transform: scale(0.5); }
    to   { opacity:1; transform: scale(1); }
  }

  h1 {
    font-family: 'Syne', sans-serif;
    font-size: 22px; font-weight: 800;
    margin-bottom: 10px;
    color: var(--heading-color);
  }

  .desc {
    font-size: 14px; color: var(--muted); line-height: 1.65;
    margin-bottom: 20px;
  }

  .info-row {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 13px;
    text-align: left;
  }
  .info-row .label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
  .info-row .value { color: var(--text); font-weight: 500; font-size: 14px; }

  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(34,211,165,0.12); border: 1px solid rgba(34,211,165,0.3);
    color: var(--green); border-radius: 999px; padding: 4px 12px;
    font-size: 12px; font-weight: 600; margin-bottom: 18px;
  }
  .badge.error-badge {
    background: rgba(244,63,94,0.12); border-color: rgba(244,63,94,0.3); color: var(--red);
  }

  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; padding: 14px;
    border-radius: 12px; border: none;
    font-size: 15px; font-weight: 600;
    text-decoration: none; cursor: pointer;
    transition: all 0.2s ease;
    margin-top: 8px;
  }
  .btn-primary {
    background: linear-gradient(135deg, var(--green), #0ea5e9);
    color: #000;
  }
  .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(34,211,165,0.3); }

  .btn-secondary {
    background: rgba(255,255,255,0.06); border: 1px solid var(--border); color: var(--text);
  }
  .btn-secondary:hover { background: rgba(255,255,255,0.1); }

  .timestamp { font-size: 11px; color: var(--muted); margin-top: 16px; }
</style>
"""

HTML_SUCCESS = (
    "<!DOCTYPE html><html lang='en'><head>"
    + _BASE_STYLE
    + """
<title>Verification Complete</title>
<style>
  :root { --accent-line: linear-gradient(90deg, var(--green), var(--blue)); --heading-color: var(--green); }
</style>
</head>
<body>
<div class="card">
  <span class="icon">✅</span>
  <div class="badge">● VERIFIED</div>
  <h1>IP Verification Complete</h1>
  <p class="desc">Your identity has been confirmed. You may now return to Telegram and continue using the bot.</p>

  <div class="info-row">
    <div><div class="label">User ID</div><div class="value">{{ user_id }}</div></div>
  </div>
  <div class="info-row">
    <div><div class="label">Detected IP</div><div class="value">{{ ip_address }}</div></div>
  </div>
  <div class="info-row">
    <div><div class="label">Status</div><div class="value" style="color:var(--green)">✓ Verified</div></div>
  </div>

  <a class="btn btn-primary" href="https://t.me">↩ Return to Telegram</a>
  <p class="timestamp">Verified at {{ timestamp }}</p>
</div>
</body></html>
"""
)

HTML_ERROR = (
    "<!DOCTYPE html><html lang='en'><head>"
    + _BASE_STYLE
    + """
<title>Verification Failed</title>
<style>
  :root { --accent-line: linear-gradient(90deg, var(--red), #f97316); --heading-color: var(--red); }
</style>
</head>
<body>
<div class="card">
  <span class="icon">❌</span>
  <div class="badge error-badge">● FAILED</div>
  <h1>Verification Failed</h1>
  <p class="desc">{{ message }}</p>

  <a class="btn btn-secondary" href="https://t.me">↩ Return to Telegram</a>
</div>
</body></html>
"""
)

# ──────────────────────────────────────────────
# Database Helpers
# ──────────────────────────────────────────────
def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_schema() -> None:
    """Create tables and add missing columns safely."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id          INTEGER PRIMARY KEY,
                username         TEXT    DEFAULT '',
                first_name       TEXT    DEFAULT '',
                balance          REAL    DEFAULT 0,
                total_earned     REAL    DEFAULT 0,
                total_withdrawn  REAL    DEFAULT 0,
                referral_count   INTEGER DEFAULT 0,
                referred_by      INTEGER DEFAULT 0,
                upi_id           TEXT    DEFAULT '',
                banned           INTEGER DEFAULT 0,
                joined_at        TEXT    DEFAULT '',
                last_daily       TEXT    DEFAULT '',
                is_premium       INTEGER DEFAULT 0,
                referral_paid    INTEGER DEFAULT 0,
                ip_address       TEXT    DEFAULT '',
                ip_verified      INTEGER DEFAULT 0,
                ip_verified_at   TEXT    DEFAULT '',
                ip_country       TEXT    DEFAULT '',
                verify_token     TEXT    DEFAULT '',
                token_expires_at INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ip_verify_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                ip_address  TEXT    NOT NULL,
                user_agent  TEXT    DEFAULT '',
                verified_at TEXT    NOT NULL,
                success     INTEGER DEFAULT 1
            )
        """)

        # Safely add any columns that might be missing (for existing databases)
        optional_columns = [
            ("referral_paid",    "INTEGER DEFAULT 0"),
            ("ip_address",       "TEXT DEFAULT ''"),
            ("ip_verified",      "INTEGER DEFAULT 0"),
            ("ip_verified_at",   "TEXT DEFAULT ''"),
            ("ip_country",       "TEXT DEFAULT ''"),
            ("verify_token",     "TEXT DEFAULT ''"),
            ("token_expires_at", "INTEGER DEFAULT 0"),
        ]
        existing = {row[1] for row in cur.execute("PRAGMA table_info(users)")}
        for col, coldef in optional_columns:
            if col not in existing:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {coldef}")
                logger.info("Added column: %s", col)

        conn.commit()
        logger.info("Database schema ready.")
    finally:
        conn.close()


def get_user(user_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user_ip(user_id: int, ip_address: str, user_agent: str = "") -> bool:
    conn = get_db()
    try:
        user = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return False
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """UPDATE users
               SET ip_address = ?, ip_verified = 1, ip_verified_at = ?,
                   verify_token = '', token_expires_at = 0
               WHERE user_id = ?""",
            (ip_address, now, user_id),
        )
        conn.execute(
            """INSERT INTO ip_verify_log (user_id, ip_address, user_agent, verified_at, success)
               VALUES (?, ?, ?, ?, 1)""",
            (user_id, ip_address, user_agent, now),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def validate_token(user_id: int, token: str) -> bool:
    """Optional: validate a one-time token tied to the user."""
    if not token:
        return True   # token not enforced if not set
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT verify_token, token_expires_at FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False
        if row["verify_token"] and row["verify_token"] != token:
            return False
        if row["token_expires_at"] and int(time.time()) > row["token_expires_at"]:
            return False
        return True
    finally:
        conn.close()

# ──────────────────────────────────────────────
# IP Helpers
# ──────────────────────────────────────────────
def get_real_ip() -> str:
    for header in ("X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP"):
        val = request.headers.get(header, "").strip()
        if val:
            return val.split(",")[0].strip()
    return request.remote_addr or ""

# ──────────────────────────────────────────────
# Telegram Notify Helper
# ──────────────────────────────────────────────
def telegram_notify(user_id: int, ip_address: str) -> None:
    """Send a silent DM to the user confirming verification."""
    if not BOT_TOKEN:
        return
    try:
        text = (
            f"✅ *IP Verified Successfully*\n\n"
            f"Your IP address has been recorded.\n"
            f"`{ip_address}`\n\n"
            f"You can now continue using the bot."
        )
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": user_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_notification": True,
            },
            timeout=5,
        )
    except Exception as exc:
        logger.warning("Telegram notify failed: %s", exc)


def telegram_notify_admin(user_id: int, ip_address: str, user_agent: str) -> None:
    """Notify admins of a new verification."""
    if not BOT_TOKEN or not ADMIN_IDS:
        return
    try:
        text = (
            f"🔔 *New IP Verification*\n\n"
            f"User ID: `{user_id}`\n"
            f"IP: `{ip_address}`\n"
            f"UA: `{user_agent[:80]}`"
        )
        for admin_id in ADMIN_IDS:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": admin_id, "text": text, "parse_mode": "Markdown"},
                timeout=5,
            )
    except Exception as exc:
        logger.warning("Admin notify failed: %s", exc)

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({"status": "ok", "service": "IP Verify Server", "version": "2.0"}), 200


@app.route("/health")
def health():
    try:
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify({"status": "ok" if db_ok else "degraded", "db": db_ok}), 200 if db_ok else 503


@app.route("/ip-verify")
def ip_verify():
    user_agent = request.headers.get("User-Agent", "")

    # ── 1. Parse & validate uid ──
    uid_raw = request.args.get("uid", "").strip()
    if not uid_raw:
        return render_template_string(HTML_ERROR, message="Missing user ID in the verification link."), 400
    if not uid_raw.isdigit():
        return render_template_string(HTML_ERROR, message="Invalid user ID format."), 400

    user_id = int(uid_raw)

    # ── 2. Validate optional token ──
    token = request.args.get("token", "").strip()
    if not validate_token(user_id, token):
        return render_template_string(
            HTML_ERROR, message="This verification link has expired or is invalid. Please request a new one from the bot."
        ), 403

    # ── 3. Detect IP ──
    ip_address = get_real_ip()
    if not ip_address:
        return render_template_string(HTML_ERROR, message="Could not detect your IP address."), 400

    # ── 4. Check user exists ──
    user = get_user(user_id)
    if not user:
        return render_template_string(
            HTML_ERROR,
            message="User not found. Please send /start to the bot first, then try again.",
        ), 404

    # ── 5. Check if banned ──
    if user.get("banned"):
        return render_template_string(HTML_ERROR, message="Your account has been suspended."), 403

    # ── 6. Write to DB ──
    ok = update_user_ip(user_id, ip_address, user_agent)
    if not ok:
        return render_template_string(HTML_ERROR, message="Database update failed. Please try again."), 500

    logger.info("Verified user_id=%s ip=%s", user_id, ip_address)

    # ── 7. Notify ──
    telegram_notify(user_id, ip_address)
    telegram_notify_admin(user_id, ip_address, user_agent)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return render_template_string(
        HTML_SUCCESS,
        user_id=user_id,
        ip_address=ip_address,
        timestamp=timestamp,
    ), 200


@app.route("/api/user/<int:user_id>/ip-status")
def user_ip_status(user_id: int):
    """Internal API endpoint to query a user's verification status."""
    # Simple token-based auth for internal calls
    auth = request.headers.get("X-Admin-Token", "")
    expected = hashlib.sha256(SECRET_KEY.encode()).hexdigest()
    if not hmac.compare_digest(auth, expected):
        return jsonify({"error": "Unauthorized"}), 401

    user = get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user_id":       user["user_id"],
        "ip_address":    user.get("ip_address", ""),
        "ip_verified":   bool(user.get("ip_verified", 0)),
        "ip_verified_at": user.get("ip_verified_at", ""),
    }), 200


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled error: %s", e)
    return render_template_string(HTML_ERROR, message="An unexpected server error occurred."), 500


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    ensure_schema()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting IP Verify Server on port %s (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
