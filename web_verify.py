from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "/data/bot_database.db")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "NeturalPredictorbot")

HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Complete</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .card {
            width: 92%;
            max-width: 420px;
            background: #1e293b;
            border-radius: 18px;
            padding: 28px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }
        h1 {
            margin-top: 0;
            font-size: 28px;
        }
        p {
            font-size: 16px;
            line-height: 1.6;
            color: #e2e8f0;
        }
        .uid {
            display: inline-block;
            margin-top: 8px;
            padding: 8px 12px;
            border-radius: 10px;
            background: #334155;
            color: #fff;
            font-weight: bold;
        }
        .btn {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 18px;
            border-radius: 10px;
            background: #22c55e;
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
        .btn:hover {
            opacity: 0.92;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>✅ Verification Complete</h1>
        <p>Your IP has been verified successfully.</p>
        <div class="uid">User ID: {{ user_id }}</div>
        <br>
        <a class="btn" href="https://t.me/{{ bot_username }}">Return to Telegram</a>
    </div>
</body>
</html>
"""

HTML_ERROR = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Failed</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .card {
            width: 92%;
            max-width: 420px;
            background: #1e293b;
            border-radius: 18px;
            padding: 28px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }
        h1 {
            margin-top: 0;
            font-size: 28px;
        }
        p {
            font-size: 16px;
            line-height: 1.6;
            color: #e2e8f0;
        }
        .btn {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 18px;
            border-radius: 10px;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
        .btn:hover {
            opacity: 0.92;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>❌ Verification Failed</h1>
        <p>{{ message }}</p>
        <a class="btn" href="https://t.me/{{ bot_username }}">Return to Telegram</a>
    </div>
</body>
</html>
"""

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_schema():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance REAL DEFAULT 0,
            total_earned REAL DEFAULT 0,
            total_withdrawn REAL DEFAULT 0,
            referral_count INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT 0,
            upi_id TEXT DEFAULT '',
            banned INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT '',
            last_daily TEXT DEFAULT '',
            is_premium INTEGER DEFAULT 0,
            referral_paid INTEGER DEFAULT 0,
            ip_address TEXT DEFAULT '',
            ip_verified INTEGER DEFAULT 0
        )
    """)

    try:
        cur.execute("ALTER TABLE users ADD COLUMN ip_address TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN ip_verified INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN referral_paid INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def get_real_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()

    return request.remote_addr or ""

def ip_used_by_other_user(ip_address, user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE ip_address = ? AND user_id != ? LIMIT 1",
        (ip_address, user_id)
    )
    row = cur.fetchone()
    conn.close()
    return row is not None

def verify_ip_for_user(user_id, ip_address):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id, ip_verified, ip_address FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = cur.fetchone()

    if not user:
        conn.close()
        return False, "User not found in database."

    if int(user["ip_verified"] or 0) == 1:
        conn.close()
        return True, "Already verified."

    if not ip_address:
        conn.close()
        return False, "Could not detect your IP address."

    if ip_used_by_other_user(ip_address, user_id):
        conn.close()
        return False, "This IP address is already used by another account."

    cur.execute(
        "UPDATE users SET ip_address = ?, ip_verified = 1 WHERE user_id = ?",
        (ip_address, user_id)
    )
    conn.commit()
    conn.close()

    return True, "Verified successfully."

@app.route("/")
def home():
    return "IP verify server is running."

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/ip-verify")
def ip_verify():
    uid = request.args.get("uid", "").strip()

    if not uid:
        return render_template_string(
            HTML_ERROR,
            message="Missing user ID in URL.",
            bot_username=BOT_USERNAME
        ), 400

    if not uid.isdigit():
        return render_template_string(
            HTML_ERROR,
            message="Invalid user ID.",
            bot_username=BOT_USERNAME
        ), 400

    user_id = int(uid)
    ip_address = get_real_ip()

    ok, message = verify_ip_for_user(user_id, ip_address)

    if not ok:
        return render_template_string(
            HTML_ERROR,
            message=message,
            bot_username=BOT_USERNAME
        ), 400

    return render_template_string(
        HTML_SUCCESS,
        user_id=user_id,
        bot_username=BOT_USERNAME
    )

if __name__ == "__main__":
    ensure_schema()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
