"""
Advanced IP Verification Server v3.0
Features: VPN/Proxy/Tor detection, risk scoring, geolocation,
          animated scanning UI, Telegram deep-link return, admin notifications.
"""

from flask import Flask, request, render_template_string, jsonify
import sqlite3, os, logging, hashlib, hmac, time, requests
from datetime import datetime, timezone

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH    = os.environ.get("DB_PATH", "/data/bot_database.db")
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "8346441928:AAFf6e7qpc8ZnF4mvLk8nXNxvIXT68AH_to")
ADMIN_IDS  = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
SECRET_KEY = os.environ.get("SECRET_KEY", hashlib.sha256(BOT_TOKEN.encode()).hexdigest())
VPNAPI_KEY = os.environ.get("VPNAPI_KEY", "")   # vpnapi.io key — free 1 000 req/day

# ─────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Security Verification</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#050b15;--s1:#0a1628;--s2:#0f1e35;
  --b1:rgba(99,179,237,.12);--b2:rgba(99,179,237,.22);
  --acc:#3b82f6;--acc2:#06b6d4;
  --gr:#10b981;--re:#ef4444;--ye:#f59e0b;
  --tx:#e2e8f0;--mu:#64748b;--mu2:#94a3b8;
  --mono:'JetBrains Mono',monospace;
  --sans:'Inter',sans-serif;
}
body{min-height:100vh;background:var(--bg);font-family:var(--sans);color:var(--tx);
  display:flex;align-items:center;justify-content:center;padding:20px;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 600px 400px at 20% 10%,rgba(59,130,246,.06) 0%,transparent 70%),
             radial-gradient(ellipse 400px 500px at 80% 90%,rgba(6,182,212,.04) 0%,transparent 70%)}
.grid-bg{position:fixed;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(99,179,237,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(99,179,237,.025) 1px,transparent 1px);
  background-size:44px 44px}
.card{width:100%;max-width:470px;background:var(--s1);border:1px solid var(--b1);
  border-radius:20px;overflow:hidden;position:relative;z-index:1;
  animation:up .45s cubic-bezier(.22,1,.36,1) both}
@keyframes up{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}
.hdr{padding:28px 28px 22px;text-align:center;
  background:linear-gradient(135deg,rgba(59,130,246,.07),rgba(6,182,212,.05));
  border-bottom:1px solid var(--b1)}
.icon{width:64px;height:64px;border-radius:50%;display:inline-flex;align-items:center;
  justify-content:center;font-size:26px;margin-bottom:14px}
.icon.ok {background:rgba(16,185,129,.1);border:2px solid rgba(16,185,129,.3);animation:glow 2.5s ease infinite}
.icon.warn{background:rgba(245,158,11,.1);border:2px solid rgba(245,158,11,.3)}
.icon.err {background:rgba(239,68,68,.1) ;border:2px solid rgba(239,68,68,.3)}
.icon.scan{background:rgba(59,130,246,.1) ;border:2px solid rgba(59,130,246,.3)}
@keyframes glow{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.4)}50%{box-shadow:0 0 0 14px rgba(16,185,129,0)}}
.ttl{font-size:18px;font-weight:600;margin-bottom:6px}
.sub{font-size:13px;color:var(--mu2);line-height:1.55}
.body{padding:18px 24px 24px}
.slbl{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--mu);margin:16px 0 8px}
.slbl:first-child{margin-top:0}
.row{display:flex;align-items:center;justify-content:space-between;
  background:var(--s2);border:1px solid var(--b1);border-radius:10px;
  padding:10px 14px;font-size:13px;margin-bottom:6px;transition:border .2s}
.row:hover{border-color:var(--b2)}
.row .lb{color:var(--mu2);display:flex;align-items:center;gap:6px;font-size:12px}
.row .vl{font-family:var(--mono);font-size:12px;font-weight:500;
  max-width:230px;word-break:break-all;text-align:right}
.chk{display:flex;align-items:center;gap:10px;background:var(--s2);
  border:1px solid var(--b1);border-radius:10px;padding:10px 14px;
  font-size:12px;margin-bottom:6px}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot.g{background:var(--gr)} .dot.r{background:var(--re)} .dot.y{background:var(--ye)} .dot.mu{background:var(--mu)}
.chk-lb{color:var(--mu2);flex:1}
.bdg{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;
  border-radius:999px;font-size:11px;font-weight:600}
.bdg.g{background:rgba(16,185,129,.13);border:1px solid rgba(16,185,129,.28);color:#10b981}
.bdg.r{background:rgba(239,68,68,.13) ;border:1px solid rgba(239,68,68,.28) ;color:#ef4444}
.bdg.y{background:rgba(245,158,11,.13);border:1px solid rgba(245,158,11,.28);color:#f59e0b}
.bdg.b{background:rgba(59,130,246,.13) ;border:1px solid rgba(59,130,246,.28) ;color:#60a5fa}
.bdg.mu{background:rgba(100,116,139,.13);border:1px solid rgba(100,116,139,.28);color:#94a3b8}
.risk-wrap{margin:14px 0 2px}
.risk-hd{display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px}
.risk-hd .lb{color:var(--mu2)}
.risk-bar{height:6px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden}
.risk-fill{height:100%;border-radius:3px;transition:width .9s cubic-bezier(.22,1,.36,1) .25s}
hr{border:none;border-top:1px solid var(--b1);margin:18px 0}
.btn{display:flex;align-items:center;justify-content:center;gap:8px;
  width:100%;padding:13px;border-radius:11px;font-size:14px;font-weight:600;
  text-decoration:none;border:none;cursor:pointer;transition:all .2s;margin-top:8px}
.btn-p{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff}
.btn-p:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(59,130,246,.35)}
.btn-g{background:rgba(255,255,255,.04);border:1px solid var(--b2);color:var(--tx)}
.btn-g:hover{background:rgba(255,255,255,.08)}
.tg-svg{width:18px;height:18px;flex-shrink:0}
.foot{border-top:1px solid var(--b1);padding:12px 24px 16px;
  text-align:center;font-size:11px;color:var(--mu)}
/* scanning */
.spin-ring{width:46px;height:46px;border:3px solid rgba(59,130,246,.15);
  border-top-color:var(--acc);border-radius:50%;animation:spin .75s linear infinite;margin:auto}
@keyframes spin{to{transform:rotate(360deg)}}
.steps{display:grid;gap:6px;margin-top:16px}
.step{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--mu);
  padding:9px 13px;background:var(--s2);border-radius:8px;border:1px solid var(--b1)}
.step.active{color:var(--acc);border-color:rgba(59,130,246,.3)}
.step.done{color:var(--gr);border-color:rgba(16,185,129,.2)}
.sdot{width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0}
</style>
</head>
<body>
<div class="grid-bg"></div>

{% if state == 'scanning' %}
<div class="card">
  <div class="hdr">
    <div class="icon scan"><div class="spin-ring"></div></div>
    <div class="ttl">Running Security Checks</div>
    <div class="sub">Analyzing your connection — please wait…</div>
  </div>
  <div class="body">
    <div class="steps">
      <div class="step" id="s1"><span class="sdot"></span>Detecting IP address</div>
      <div class="step" id="s2"><span class="sdot"></span>VPN / Proxy analysis</div>
      <div class="step" id="s3"><span class="sdot"></span>Tor exit-node check</div>
      <div class="step" id="s4"><span class="sdot"></span>Geolocation &amp; ISP lookup</div>
      <div class="step" id="s5"><span class="sdot"></span>Verifying user account</div>
      <div class="step" id="s6"><span class="sdot"></span>Saving verification record</div>
    </div>
  </div>
  <div class="foot">Secured by bot verification system</div>
</div>
<script>
const ids=['s1','s2','s3','s4','s5','s6'];let i=0;
function next(){
  if(i>0)ids[i-1]&&(document.getElementById(ids[i-1]).className='step done');
  if(i<ids.length){document.getElementById(ids[i]).className='step active';i++;setTimeout(next,550+Math.random()*350);}
  else setTimeout(()=>{location.href='{{ redirect_url }}';},250);
}
setTimeout(next,300);
</script>

{% elif state == 'success' %}
<div class="card">
  <div class="hdr">
    <div class="icon ok">✓</div>
    <div class="ttl" style="color:#10b981">Verification Complete</div>
    <div class="sub">Your connection has been verified and securely recorded.</div>
  </div>
  <div class="body">
    <div class="slbl">Connection info</div>
    <div class="row"><span class="lb">&#127758; IP Address</span><span class="vl">{{ ip_address }}</span></div>
    <div class="row"><span class="lb">&#128205; Location</span><span class="vl">{{ location }}</span></div>
    <div class="row"><span class="lb">&#127970; ISP / Org</span><span class="vl">{{ isp }}</span></div>
    <div class="row"><span class="lb">&#128100; User ID</span><span class="vl">{{ user_id }}</span></div>

    <div class="slbl">Security checks</div>
    <div class="chk">
      <span class="dot {{ 'r' if vpn else 'g' }}"></span>
      <span class="chk-lb">VPN Detection</span>
      <span class="bdg {{ 'r' if vpn else 'g' }}">{{ 'VPN Detected' if vpn else 'Clean' }}</span>
    </div>
    <div class="chk">
      <span class="dot {{ 'r' if proxy else 'g' }}"></span>
      <span class="chk-lb">Proxy / Relay</span>
      <span class="bdg {{ 'r' if proxy else 'g' }}">{{ 'Proxy Found' if proxy else 'None' }}</span>
    </div>
    <div class="chk">
      <span class="dot {{ 'r' if tor else 'g' }}"></span>
      <span class="chk-lb">Tor Exit Node</span>
      <span class="bdg {{ 'r' if tor else 'g' }}">{{ 'Tor Detected' if tor else 'Clean' }}</span>
    </div>
    <div class="chk">
      <span class="dot {{ 'y' if dc else 'g' }}"></span>
      <span class="chk-lb">Datacenter / Hosting IP</span>
      <span class="bdg {{ 'y' if dc else 'g' }}">{{ 'Datacenter' if dc else 'Residential' }}</span>
    </div>
    <div class="chk">
      <span class="dot g"></span>
      <span class="chk-lb">Account Status</span>
      <span class="bdg g">Active</span>
    </div>

    <div class="risk-wrap">
      <div class="risk-hd">
        <span class="lb">Risk Score</span>
        <span style="font-weight:600;color:{{ '#ef4444' if risk>65 else '#f59e0b' if risk>30 else '#10b981' }}">{{ risk }}/100</span>
      </div>
      <div class="risk-bar">
        <div class="risk-fill" id="rf"
          style="width:0%;background:{{ '#ef4444' if risk>65 else '#f59e0b' if risk>30 else '#10b981' }}"></div>
      </div>
    </div>

    <hr>
    <a class="btn btn-p" href="{{ tg_link }}">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Return to Telegram
    </a>
    <button class="btn btn-g" onclick="copyIP()">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      <span id="cplbl">Copy IP Address</span>
    </button>
    <p style="text-align:center;font-size:11px;color:var(--mu);margin-top:14px">Verified at {{ ts }}</p>
  </div>
  <div class="foot">Bot Security System &bull; All checks complete</div>
</div>
<script>
setTimeout(()=>{ document.getElementById('rf').style.width='{{ risk }}%'; },200);
function copyIP(){
  navigator.clipboard.writeText('{{ ip_address }}').then(()=>{
    const l=document.getElementById('cplbl');l.textContent='Copied!';
    setTimeout(()=>l.textContent='Copy IP Address',2000);
  });
}
</script>

{% elif state == 'flagged' %}
<div class="card">
  <div class="hdr">
    <div class="icon warn">⚠</div>
    <div class="ttl" style="color:#f59e0b">Connection Flagged</div>
    <div class="sub">Verified, but security issues were detected on your connection.</div>
  </div>
  <div class="body">
    {% for f in flags %}
    <div class="chk"><span class="dot r"></span><span class="chk-lb">{{ f }}</span><span class="bdg r">Flagged</span></div>
    {% endfor %}
    <hr>
    <p style="font-size:13px;color:var(--mu2);line-height:1.6;margin-bottom:14px">
      Your verification was recorded, but anonymizing tools were detected.
      Some bot features may be limited.
    </p>
    <a class="btn btn-p" href="{{ tg_link }}">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Return to Telegram
    </a>
  </div>
  <div class="foot">Bot Security System</div>
</div>

{% else %}
<div class="card">
  <div class="hdr">
    <div class="icon err">✕</div>
    <div class="ttl" style="color:#ef4444">Verification Failed</div>
    <div class="sub">{{ message }}</div>
  </div>
  <div class="body">
    <a class="btn btn-p" href="{{ tg_link }}">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Return to Telegram
    </a>
    <button class="btn btn-g" onclick="location.reload()">Try Again</button>
  </div>
  <div class="foot">Bot Security System</div>
</div>
{% endif %}
</body></html>
"""

# ─────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────
def get_db():
    d = os.path.dirname(DB_PATH)
    if d:
        os.makedirs(d, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_schema():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id          INTEGER PRIMARY KEY,
                username         TEXT DEFAULT '',first_name TEXT DEFAULT '',
                balance          REAL DEFAULT 0,total_earned REAL DEFAULT 0,
                total_withdrawn  REAL DEFAULT 0,referral_count INTEGER DEFAULT 0,
                referred_by      INTEGER DEFAULT 0,upi_id TEXT DEFAULT '',
                banned           INTEGER DEFAULT 0,joined_at TEXT DEFAULT '',
                last_daily       TEXT DEFAULT '',is_premium INTEGER DEFAULT 0,
                referral_paid    INTEGER DEFAULT 0,
                ip_address       TEXT DEFAULT '',ip_verified INTEGER DEFAULT 0,
                ip_verified_at   TEXT DEFAULT '',ip_country TEXT DEFAULT '',
                ip_isp           TEXT DEFAULT '',ip_risk_score INTEGER DEFAULT 0,
                vpn_detected     INTEGER DEFAULT 0,proxy_detected INTEGER DEFAULT 0,
                tor_detected     INTEGER DEFAULT 0,datacenter INTEGER DEFAULT 0,
                verify_token     TEXT DEFAULT '',token_expires_at INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS ip_verify_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,ip_address TEXT NOT NULL,
                user_agent  TEXT DEFAULT '',country TEXT DEFAULT '',
                isp         TEXT DEFAULT '',vpn INTEGER DEFAULT 0,
                proxy       INTEGER DEFAULT 0,tor INTEGER DEFAULT 0,
                datacenter  INTEGER DEFAULT 0,risk_score INTEGER DEFAULT 0,
                verified_at TEXT NOT NULL,success INTEGER DEFAULT 1
            )
        """)
        existing = {r[1] for r in c.execute("PRAGMA table_info(users)")}
        new_cols = [
            ("ip_isp","TEXT DEFAULT ''"),("ip_risk_score","INTEGER DEFAULT 0"),
            ("vpn_detected","INTEGER DEFAULT 0"),("proxy_detected","INTEGER DEFAULT 0"),
            ("tor_detected","INTEGER DEFAULT 0"),("datacenter","INTEGER DEFAULT 0"),
            ("ip_verified_at","TEXT DEFAULT ''"),("ip_country","TEXT DEFAULT ''"),
            ("verify_token","TEXT DEFAULT ''"),("token_expires_at","INTEGER DEFAULT 0"),
            ("referral_paid","INTEGER DEFAULT 0"),
        ]
        for col, coldef in new_cols:
            if col not in existing:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {coldef}")
                except Exception:
                    pass
        conn.commit()
        logger.info("DB schema ready.")
    finally:
        conn.close()


def get_user(uid: int):
    conn = get_db()
    try:
        r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def save_verification(uid, ip, sec: dict, ua="") -> bool:
    conn = get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE users SET
              ip_address=?,ip_verified=1,ip_verified_at=?,ip_country=?,ip_isp=?,
              ip_risk_score=?,vpn_detected=?,proxy_detected=?,tor_detected=?,datacenter=?,
              verify_token='',token_expires_at=0
            WHERE user_id=?
        """, (ip, now, sec.get("country",""), sec.get("isp",""), sec.get("risk_score",0),
              int(sec.get("vpn",False)), int(sec.get("proxy",False)),
              int(sec.get("tor",False)),  int(sec.get("dc",False)), uid))
        conn.execute("""
            INSERT INTO ip_verify_log
              (user_id,ip_address,user_agent,country,isp,vpn,proxy,tor,datacenter,risk_score,verified_at,success)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,1)
        """, (uid, ip, ua, sec.get("country",""), sec.get("isp",""),
              int(sec.get("vpn",False)), int(sec.get("proxy",False)),
              int(sec.get("tor",False)),  int(sec.get("dc",False)),
              sec.get("risk_score",0), now))
        conn.commit()
        return True
    except Exception as e:
        logger.error("DB error: %s", e)
        return False
    finally:
        conn.close()


def validate_token(uid, token) -> bool:
    if not token:
        return True
    conn = get_db()
    try:
        r = conn.execute("SELECT verify_token,token_expires_at FROM users WHERE user_id=?", (uid,)).fetchone()
        if not r:
            return False
        if r["verify_token"] and r["verify_token"] != token:
            return False
        if r["token_expires_at"] and int(time.time()) > r["token_expires_at"]:
            return False
        return True
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# IP Analysis
# ─────────────────────────────────────────────────────────────
def get_real_ip() -> str:
    for h in ("CF-Connecting-IP","X-Forwarded-For","X-Real-IP"):
        v = request.headers.get(h,"").strip()
        if v:
            return v.split(",")[0].strip()
    return request.remote_addr or ""


def analyze_ip(ip: str) -> dict:
    res = {"vpn":False,"proxy":False,"tor":False,"dc":False,
           "country":"Unknown","isp":"Unknown","location":"Unknown","risk_score":0}
    if not ip or any(ip.startswith(p) for p in ("127.","10.","192.168.","::1")):
        res.update({"location":"Local Network","isp":"Private"})
        return res
    try:
        if VPNAPI_KEY:
            r = requests.get(f"https://vpnapi.io/api/{ip}?key={VPNAPI_KEY}", timeout=5).json()
            sec = r.get("security",{})
            loc = r.get("location",{})
            net = r.get("network",{})
            res["vpn"]     = bool(sec.get("vpn"))
            res["proxy"]   = bool(sec.get("proxy"))
            res["tor"]     = bool(sec.get("tor"))
            res["dc"]      = bool(sec.get("relay"))
            res["country"] = loc.get("country","Unknown")
            city = loc.get("city","")
            res["location"]= f"{city}, {loc.get('country','')}" if city else loc.get("country","Unknown")
            res["isp"]     = net.get("autonomous_system_organization","Unknown")
        else:
            # ip-api.com — free, no key needed
            r = requests.get(
                f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,proxy,hosting,as",
                timeout=5
            ).json()
            if r.get("status") == "success":
                res["proxy"]   = bool(r.get("proxy"))
                res["dc"]      = bool(r.get("hosting"))
                res["country"] = r.get("country","Unknown")
                city   = r.get("city","")
                region = r.get("regionName","")
                res["location"] = ", ".join(x for x in [city,region,r.get("country","")] if x)
                res["isp"]      = r.get("isp") or r.get("org","Unknown")
    except Exception as e:
        logger.warning("IP analysis error: %s", e)
    score = 0
    if res["vpn"]:   score += 40
    if res["proxy"]: score += 35
    if res["tor"]:   score += 60
    if res["dc"]:    score += 20
    res["risk_score"] = min(score, 100)
    return res

# ─────────────────────────────────────────────────────────────
# Telegram
# ─────────────────────────────────────────────────────────────
_bot_username = None

def get_bot_username() -> str:
    global _bot_username
    if _bot_username:
        return _bot_username
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=4).json()
        if r.get("ok"):
            _bot_username = r["result"].get("username","")
            return _bot_username
    except Exception:
        pass
    return ""


def tg_link(param="verified") -> str:
    u = get_bot_username()
    return f"https://t.me/{u}?start={param}" if u else "https://t.me"


def tg_send(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id":chat_id,"text":text,"parse_mode":"Markdown","disable_notification":True},
            timeout=5
        )
    except Exception as e:
        logger.warning("tg send fail %s: %s", chat_id, e)


def notify_user(uid, ip, sec):
    flags = []
    if sec.get("vpn"):   flags.append("🔴 VPN")
    if sec.get("proxy"): flags.append("🔴 Proxy")
    if sec.get("tor"):   flags.append("🔴 Tor")
    if sec.get("dc"):    flags.append("🟡 Datacenter IP")
    status = "⚠️ *Flags:* " + ", ".join(flags) if flags else "✅ Connection is clean"
    tg_send(uid,
        f"✅ *IP Verification Complete*\n\n"
        f"📍 IP: `{ip}`\n"
        f"🌍 Location: {sec.get('location','?')}\n"
        f"🏢 ISP: {sec.get('isp','?')}\n"
        f"⚡ Risk Score: {sec.get('risk_score',0)}/100\n\n{status}"
    )


def notify_admins(uid, ip, sec, ua):
    if not ADMIN_IDS:
        return
    flags = [k for k,v in [("VPN",sec.get("vpn")),("Proxy",sec.get("proxy")),
                             ("Tor",sec.get("tor")),("DC",sec.get("dc"))] if v]
    text = (
        f"🔔 *New Verification*\n\n"
        f"User: `{uid}`\nIP: `{ip}`\n"
        f"Country: {sec.get('country','?')}\nISP: {sec.get('isp','?')}\n"
        f"Flags: {' | '.join(flags) or 'None'}\n"
        f"Risk: {sec.get('risk_score',0)}/100\nUA: `{ua[:70]}`"
    )
    for aid in ADMIN_IDS:
        tg_send(aid, text)

# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({"status":"ok","service":"IP Verify Server","version":"3.0"}), 200


@app.route("/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone(); db=True
    except Exception:
        db=False
    return jsonify({"db":db}), 200 if db else 503


def err_page(msg, code=400):
    return render_template_string(HTML, state="error", message=msg, tg_link=tg_link()), code


@app.route("/ip-verify")
def ip_verify():
    uid_raw = request.args.get("uid","").strip()
    token   = request.args.get("token","").strip()
    if not uid_raw or not uid_raw.isdigit():
        return err_page("Invalid or missing user ID in link.")
    uid = int(uid_raw)
    if not validate_token(uid, token):
        return err_page("This link has expired. Please request a new one from the bot.", 403)
    if not get_real_ip():
        return err_page("Could not detect your IP address.")
    user = get_user(uid)
    if not user:
        return err_page("User not found. Send /start to the bot first.", 404)
    if user.get("banned"):
        return err_page("Your account has been suspended.", 403)
    rurl = f"/ip-verify-result?uid={uid}" + (f"&token={token}" if token else "")
    return render_template_string(HTML, state="scanning", redirect_url=rurl), 200


@app.route("/ip-verify-result")
def ip_verify_result():
    ua      = request.headers.get("User-Agent","")
    uid_raw = request.args.get("uid","").strip()
    token   = request.args.get("token","").strip()
    if not uid_raw or not uid_raw.isdigit():
        return err_page("Invalid user ID.")
    uid = int(uid_raw)
    if not validate_token(uid, token):
        return err_page("Link expired.", 403)
    ip   = get_real_ip()
    user = get_user(uid)
    if not user:
        return err_page("User not found.", 404)
    if user.get("banned"):
        return err_page("Account suspended.", 403)

    sec = analyze_ip(ip)
    if not save_verification(uid, ip, sec, ua):
        return err_page("Database error. Please try again.", 500)

    notify_user(uid, ip, sec)
    notify_admins(uid, ip, sec, ua)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    flags = []
    if sec.get("vpn"):   flags.append("VPN / Tunnel detected")
    if sec.get("proxy"): flags.append("HTTP Proxy detected")
    if sec.get("tor"):   flags.append("Tor exit node")
    if sec.get("dc"):    flags.append("Datacenter / Hosting IP")

    state = "flagged" if flags and sec["risk_score"] >= 35 else "success"
    return render_template_string(HTML,
        state=state, user_id=uid, ip_address=ip,
        location=sec.get("location","Unknown"), isp=sec.get("isp","Unknown"),
        vpn=sec.get("vpn",False), proxy=sec.get("proxy",False),
        tor=sec.get("tor",False), dc=sec.get("dc",False),
        risk=sec.get("risk_score",0), flags=flags, ts=ts,
        tg_link=tg_link("verified")
    ), 200


@app.route("/api/user/<int:uid>/ip-status")
def user_ip_status(uid: int):
    auth = request.headers.get("X-Admin-Token","")
    expected = hashlib.sha256(SECRET_KEY.encode()).hexdigest()
    if not hmac.compare_digest(auth, expected):
        return jsonify({"error":"Unauthorized"}), 401
    user = get_user(uid)
    if not user:
        return jsonify({"error":"Not found"}), 404
    return jsonify({
        "user_id":     user["user_id"],
        "ip_address":  user.get("ip_address",""),
        "ip_verified": bool(user.get("ip_verified",0)),
        "verified_at": user.get("ip_verified_at",""),
        "country":     user.get("ip_country",""),
        "isp":         user.get("ip_isp",""),
        "risk_score":  user.get("ip_risk_score",0),
        "vpn":         bool(user.get("vpn_detected",0)),
        "proxy":       bool(user.get("proxy_detected",0)),
        "tor":         bool(user.get("tor_detected",0)),
        "datacenter":  bool(user.get("datacenter",0)),
    }), 200


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error":"Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.exception("500: %s", e)
    return err_page("An unexpected server error occurred.")


if __name__ == "__main__":
    ensure_schema()
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG","false").lower() == "true"
    logger.info("Starting on port %s (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
