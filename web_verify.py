from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "/data/bot_database.db"

HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Verification Complete</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .box {
            width: 90%;
            max-width: 430px;
            background: rgba(30, 41, 59, 0.95);
            border-radius: 18px;
            padding: 30px 24px;
            text-align: center;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
        }
        h1 {
            margin: 0 0 14px 0;
            font-size: 26px;
            color: #22c55e;
        }
        p {
            margin: 10px 0;
            color: #cbd5e1;
            line-height: 1.6;
            font-size: 15px;
        }
        code {
            display: inline-block;
            background: #334155;
            padding: 5px 10px;
            border-radius: 8px;
            color: #ffffff;
            font-size: 14px;
            margin-top: 4px;
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
            transition: 0.2s ease;
        }
        .btn:hover {
            background: #16a34a;
        }
        .small {
            font-size: 13px;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>✅ IP Verification Complete</h1>
        <p>Your IP has been successfully verified.</p>
        <p>User ID:</p>
        <code>{{ user_id }}</code>
        <p class="small">You can now return to Telegram and continue.</p>
        <a class="btn" href="https://t.me">Return to Telegram</a>
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
    <title>Verification Error</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .box {
            width: 90%;
            max-width: 430px;
            background: rgba(30, 41, 59, 0.95);
            border-radius: 18px;
            padding: 30px 24px;
            text-align: center;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
        }
        h1 {
            margin: 0 0 14px 0;
            font-size: 24px;
            color: #ef4444;
        }
        p {
            margin: 10px 0;
            color: #cbd5e1;
            line-height: 1.6;
            font-size: 15px;
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
            transition: 0.2s ease;
        }
        .btn:hover {
            background: #2563eb;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>❌ Verification Failed</h1>
        <p>{{ message }}</p>
        <a class="btn" href="https://t.me">Return to Telegram</a>
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
        cur.execute("ALTER TABLE users ADD COLUMN referral_paid INTEGER DEFAULT 0")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN ip_address TEXT DEFAULT ''")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN ip_verified INTEGER DEFAULT 0")
    except:
        pass

    conn.commit()
    conn.close()

def update_user_ip(user_id: int, ip_address: str) -> bool:
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return False

    cur.execute(
        "UPDATE users SET ip_address = ?, ip_verified = 1 WHERE user_id = ?",
        (ip_address, user_id)
    )
    conn.commit()
    conn.close()
    return True

def get_real_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()

    return request.remote_addr or ""

@app.route("/")
def home():
    return "IP verify server is running."

@app.route("/ip-verify")
def ip_verify():
    try:
        user_id_raw = request.args.get("uid", "").strip()

        if not user_id_raw:
            return render_template_string(
                HTML_ERROR,
                message="Missing user ID in verification link."
            ), 400

        if not user_id_raw.isdigit():
            return render_template_string(
                HTML_ERROR,
                message="Invalid user ID."
            ), 400

        user_id = int(user_id_raw)
        ip_address = get_real_ip()

        if not ip_address:
            return render_template_string(
                HTML_ERROR,
                message="Could not detect your IP address."
            ), 400

        ok = update_user_ip(user_id, ip_address)
        if not ok:
            return render_template_string(
                HTML_ERROR,
                message="User not found in database. Please start the bot first."
            ), 404

        return render_template_string(HTML_SUCCESS, user_id=user_id)

    except Exception as e:
        return render_template_string(
            HTML_ERROR,
            message=f"Server error: {str(e)}"
        ), 500

if __name__ == "__main__":
    ensure_user_columns()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
