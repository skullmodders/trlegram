from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "/data/bot_database.db")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "neturalpredictorbot")

HTML_SUCCESS = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Complete</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .box {
            width: 90%;
            max-width: 420px;
            background: #1e293b;
            border-radius: 16px;
            padding: 28px;
            text-align: center;
        }
        .btn {
            display: inline-block;
            margin-top: 18px;
            padding: 12px 20px;
            border-radius: 10px;
            background: #22c55e;
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
        code {
            background: #334155;
            padding: 5px 10px;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>✅ Verification Complete</h1>
        <p>Your IP has been verified successfully.</p>
        <p>User ID: <code>{{ user_id }}</code></p>
        <a class="btn" href="https://t.me/{{ bot_username }}">Return to Telegram</a>
    </div>
</body>
</html>
"""

HTML_ERROR = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Failed</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .box {
            width: 90%;
            max-width: 420px;
            background: #1e293b;
            border-radius: 16px;
            padding: 28px;
            text-align: center;
        }
        .btn {
            display: inline-block;
            margin-top: 18px;
            padding: 12px 20px;
            border-radius: 10px;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="box">
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

def ensure_user_columns():
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
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN ip_verified INTEGER DEFAULT 0")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN referral_paid INTEGER DEFAULT 0")
    except:
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

def is_ip_already_used(ip_address, user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE ip_address = ? AND user_id != ? LIMIT 1",
        (ip_address, user_id)
    )
    row = cur.fetchone()
    conn.close()
    return row is not None

def verify_user_ip(user_id, ip_address):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id, ip_verified FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return False, "User not found."

    if int(user["ip_verified"] or 0) == 1:
        conn.close()
        return True, "Already verified."

    if is_ip_already_used(ip_address, user_id):
        conn.close()
        return False, "This IP address has already been used by another account."

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

@app.route("/ip-verify")
def ip_verify():
    user_id_raw = request.args.get("uid", "").strip()

    if not user_id_raw:
        return render_template_string(
            HTML_ERROR,
            message="Missing user ID in verification link.",
            bot_username=BOT_USERNAME
        ), 400

    if not user_id_raw.isdigit():
        return render_template_string(
            HTML_ERROR,
            message="Invalid user ID.",
            bot_username=BOT_USERNAME
        ), 400

    user_id = int(user_id_raw)
    ip_address = get_real_ip()

    if not ip_address:
        return render_template_string(
            HTML_ERROR,
            message="Could not detect your IP address.",
            bot_username=BOT_USERNAME
        ), 400

    ok, message = verify_user_ip(user_id, ip_address)

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
    ensure_user_columns()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
