"""
IP Verification + Channel Join Check Server — v4.0
Railway-ready | Flask | VPN/Proxy/Tor detection | Channel verification
"""

from flask import Flask, request, render_template_string, jsonify
import sqlite3, os, logging, hashlib, hmac, time, requests
from datetime import datetime, timezone

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
DB_PATH    = os.environ.get("DB_PATH", "/data/bot_database.db")
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "8346441928:AAFf6e7qpc8ZnF4mvLk8nXNxvIXT68AH_to")
SECRET_KEY = os.environ.get("SECRET_KEY", hashlib.sha256(BOT_TOKEN.encode()).hexdigest())
VPNAPI_KEY = os.environ.get("VPNAPI_KEY", "")        # vpnapi.io — free 1 000 req/day
ADMIN_IDS  = [int(x) for x in os.environ.get("ADMIN_IDS","").split(",") if x.strip().isdigit()]

# Channels that must be joined (can also be read from DB settings at runtime)
FORCE_JOIN_CHANNELS = os.environ.get(
    "FORCE_JOIN_CHANNELS",
    "@skullmodder,@botsarefather,@upilootpay"
).split(",")
FORCE_JOIN_CHANNELS = [c.strip() for c in FORCE_JOIN_CHANNELS if c.strip()]

# ── HTML ─────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Verification · UPI Loot Pay</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@500;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;1,9..40,400&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#0a0f1e;--paper:#f4f6fb;--surface:#ffffff;--surface2:#f0f3fa;
  --border:rgba(30,60,180,.08);--border2:rgba(30,60,180,.16);
  --blue:#2563eb;--blue2:#1d4ed8;--cyan:#0ea5e9;
  --green:#059669;--green2:#047857;
  --red:#dc2626;--amber:#d97706;
  --text:#0f172a;--muted:#64748b;--muted2:#94a3b8;
  --mono:'DM Mono',ui-monospace,monospace;
  --sans:'DM Sans',sans-serif;--disp:'Syne',sans-serif;
}
html{-webkit-text-size-adjust:100%}
body{
  min-height:100vh;
  background:var(--paper);
  font-family:var(--sans);color:var(--text);
  display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start;
  padding:24px 16px 48px;
  position:relative;
}
/* Subtle geometric bg */
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    radial-gradient(ellipse 700px 500px at 10% 0%,rgba(37,99,235,.05) 0%,transparent 65%),
    radial-gradient(ellipse 500px 700px at 90% 100%,rgba(14,165,233,.04) 0%,transparent 65%);
}
.geo{
  position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
}
.geo svg{position:absolute;opacity:.04}
.geo svg:nth-child(1){top:-80px;right:-80px;width:400px}
.geo svg:nth-child(2){bottom:-60px;left:-60px;width:300px}

/* Wordmark */
.wordmark{
  font-family:var(--disp);font-size:13px;font-weight:700;
  letter-spacing:.12em;text-transform:uppercase;
  color:var(--blue);opacity:.7;margin-bottom:28px;margin-top:8px;
  position:relative;z-index:1;
}

/* Card */
.card{
  width:100%;max-width:460px;
  background:var(--surface);
  border:1px solid var(--border2);
  border-radius:24px;
  overflow:hidden;
  position:relative;z-index:1;
  box-shadow:0 1px 3px rgba(0,0,0,.04),0 8px 32px rgba(30,60,180,.06);
  animation:riseIn .5s cubic-bezier(.22,1,.36,1) both;
}
@keyframes riseIn{from{opacity:0;transform:translateY(28px) scale(.98)}to{opacity:1;transform:none}}

/* Progress bar at top of card */
.card-progress{
  height:3px;
  background:linear-gradient(90deg,var(--blue),var(--cyan));
  transform-origin:left;
  animation:none;
}
.card-progress.animate{animation:progFill 2.4s ease both}
@keyframes progFill{from{transform:scaleX(0)}to{transform:scaleX(1)}}

.card-head{
  padding:28px 28px 22px;
  border-bottom:1px solid var(--border);
  display:flex;flex-direction:column;align-items:center;text-align:center;
  gap:12px;
}
.status-ring{
  width:72px;height:72px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:30px;position:relative;flex-shrink:0;
}
.ring-ok   {background:#ecfdf5;border:2px solid #a7f3d0}
.ring-warn {background:#fffbeb;border:2px solid #fde68a}
.ring-err  {background:#fef2f2;border:2px solid #fecaca}
.ring-scan {background:#eff6ff;border:2px solid #bfdbfe}
.ring-join {background:#f0fdf4;border:2px solid #bbf7d0}

/* Pulse for success */
@keyframes pulseRing{
  0%,100%{box-shadow:0 0 0 0 rgba(5,150,105,.3)}
  50%{box-shadow:0 0 0 12px rgba(5,150,105,0)}
}
.ring-ok{animation:pulseRing 2.5s ease infinite}

.head-title{font-family:var(--disp);font-size:19px;font-weight:700;line-height:1.2}
.head-sub{font-size:13px;color:var(--muted);line-height:1.55;max-width:300px}
.card-body{padding:20px 24px 26px}

/* Section label */
.sec{
  font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted2);margin:18px 0 8px;
}
.sec:first-child{margin-top:0}

/* Info rows */
.irow{
  display:flex;align-items:center;justify-content:space-between;
  gap:12px;
  background:var(--surface2);
  border:1px solid var(--border);border-radius:12px;
  padding:11px 14px;margin-bottom:7px;
  transition:border-color .15s;
}
.irow:hover{border-color:var(--border2)}
.irow-lbl{
  display:flex;align-items:center;gap:8px;
  font-size:12px;color:var(--muted);font-weight:500;white-space:nowrap;
}
.irow-lbl svg{width:14px;height:14px;stroke:currentColor;flex-shrink:0}
.irow-val{
  font-size:12px;font-weight:600;color:var(--text);
  text-align:right;word-break:break-all;max-width:220px;
}

/* Badges */
.badge{
  display:inline-flex;align-items:center;gap:4px;
  padding:2px 9px;border-radius:99px;
  font-size:11px;font-weight:700;letter-spacing:.02em;
}
.b-ok  {background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0}
.b-warn{background:#fffbeb;color:#92400e;border:1px solid #fde68a}
.b-err {background:#fef2f2;color:#991b1b;border:1px solid #fecaca}
.b-blue{background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe}
.b-gray{background:#f8fafc;color:#475569;border:1px solid #e2e8f0}

/* Security check items */
.checks{display:grid;gap:6px}
.chk{
  display:flex;align-items:center;gap:10px;
  background:var(--surface2);border:1px solid var(--border);
  border-radius:10px;padding:10px 14px;
}
.chk-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.dot-g{background:var(--green)} .dot-r{background:var(--red)}
.dot-y{background:var(--amber)} .dot-mu{background:var(--muted2)}
.chk-lbl{flex:1;font-size:12px;color:var(--muted);font-weight:500}
.chk-val{font-size:11px;font-weight:700}

/* Risk bar */
.risk-wrap{margin:14px 0 4px}
.risk-hd{display:flex;justify-content:space-between;font-size:12px;margin-bottom:7px;font-weight:500}
.risk-hd .rl{color:var(--muted)}
.risk-track{height:7px;background:var(--surface2);border-radius:4px;overflow:hidden;border:1px solid var(--border)}
.risk-fill{height:100%;border-radius:4px;transition:width .9s cubic-bezier(.22,1,.36,1) .3s;width:0%}

/* Channel join list */
.ch-list{display:grid;gap:8px;margin-bottom:4px}
.ch-item{
  display:flex;align-items:center;gap:12px;
  background:var(--surface2);border:1px solid var(--border);
  border-radius:12px;padding:12px 14px;
}
.ch-avatar{
  width:38px;height:38px;border-radius:50%;
  background:linear-gradient(135deg,var(--blue),var(--cyan));
  display:flex;align-items:center;justify-content:center;
  font-size:16px;flex-shrink:0;color:#fff;font-weight:700;
  font-family:var(--disp);
}
.ch-info{flex:1;min-width:0}
.ch-name{font-size:13px;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ch-handle{font-size:11px;color:var(--muted);margin-top:1px}
.ch-status{flex-shrink:0}
.ch-joined{color:var(--green);font-size:18px}
.ch-pending{color:var(--muted2);font-size:18px}

/* Divider */
hr{border:none;border-top:1px solid var(--border);margin:18px 0}

/* Buttons */
.btn{
  display:flex;align-items:center;justify-content:center;gap:9px;
  width:100%;padding:14px;border-radius:13px;
  font-size:14px;font-weight:700;font-family:var(--sans);
  text-decoration:none;border:none;cursor:pointer;
  transition:transform .15s,box-shadow .15s;margin-top:9px;
  letter-spacing:.01em;
}
.btn:active{transform:scale(.98)}
.btn-primary{
  background:linear-gradient(135deg,var(--blue),var(--blue2));
  color:#fff;
  box-shadow:0 4px 14px rgba(37,99,235,.3);
}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(37,99,235,.35)}
.btn-green{
  background:linear-gradient(135deg,var(--green),var(--green2));
  color:#fff;
  box-shadow:0 4px 14px rgba(5,150,105,.25);
}
.btn-green:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(5,150,105,.3)}
.btn-ghost{
  background:var(--surface2);border:1px solid var(--border2);
  color:var(--text);
}
.btn-ghost:hover{background:#e8edf8}
.tg-svg{width:18px;height:18px;flex-shrink:0}

/* Spinner & scanning */
.spin{
  width:42px;height:42px;
  border:3px solid var(--border2);
  border-top-color:var(--blue);
  border-radius:50%;
  animation:sp .75s linear infinite;
}
@keyframes sp{to{transform:rotate(360deg)}}

.steps{display:grid;gap:6px;margin-top:8px}
.step{
  display:flex;align-items:center;gap:10px;
  font-size:12px;color:var(--muted2);font-weight:500;
  padding:9px 13px;background:var(--surface2);
  border-radius:9px;border:1px solid var(--border);
  transition:all .2s;
}
.step.active{
  color:var(--blue);background:#eff6ff;
  border-color:rgba(37,99,235,.25);
}
.step.done{
  color:var(--green);background:#ecfdf5;
  border-color:rgba(5,150,105,.2);
}
.sdot{width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0}

/* Timestamp */
.ts{text-align:center;font-size:11px;color:var(--muted2);margin-top:14px}

/* Footer */
.foot{
  border-top:1px solid var(--border);
  padding:12px 24px 16px;
  text-align:center;font-size:11px;color:var(--muted2);
  display:flex;align-items:center;justify-content:center;gap:6px;
}
.foot svg{width:13px;height:13px;stroke:currentColor;opacity:.6}

/* Copy btn */
.copy-btn{
  background:none;border:1px solid var(--border2);
  border-radius:8px;padding:4px 10px;
  font-size:11px;font-weight:600;color:var(--muted);
  cursor:pointer;transition:.15s;margin-left:6px;
}
.copy-btn:hover{background:var(--surface2);color:var(--text)}
</style>
</head>
<body>
<div class="geo">
  <svg viewBox="0 0 200 200" style="top:-60px;right:-60px"><circle cx="100" cy="100" r="90" fill="none" stroke="#2563eb" stroke-width="1.5"/><circle cx="100" cy="100" r="60" fill="none" stroke="#2563eb" stroke-width="1"/><circle cx="100" cy="100" r="30" fill="none" stroke="#2563eb" stroke-width=".8"/></svg>
  <svg viewBox="0 0 160 160" style="bottom:-40px;left:-40px"><rect x="20" y="20" width="120" height="120" rx="18" fill="none" stroke="#0ea5e9" stroke-width="1.2"/><rect x="45" y="45" width="70" height="70" rx="10" fill="none" stroke="#0ea5e9" stroke-width=".8"/></svg>
</div>

<div class="wordmark">UPI Loot Pay</div>

{# ─── SCANNING STATE ─────────────────────────────────────────────────────── #}
{% if state == 'scanning' %}
<div class="card">
  <div class="card-progress animate"></div>
  <div class="card-head">
    <div class="status-ring ring-scan" style="flex-direction:column;gap:0">
      <div class="spin"></div>
    </div>
    <div>
      <div class="head-title">Running Security Checks</div>
      <div class="head-sub">Analyzing your connection — please wait a moment</div>
    </div>
  </div>
  <div class="card-body">
    <div class="sec">Progress</div>
    <div class="steps">
      <div class="step" id="s1"><span class="sdot"></span>Detecting your IP address</div>
      <div class="step" id="s2"><span class="sdot"></span>VPN &amp; proxy analysis</div>
      <div class="step" id="s3"><span class="sdot"></span>Tor exit-node check</div>
      <div class="step" id="s4"><span class="sdot"></span>Geolocation &amp; ISP lookup</div>
      <div class="step" id="s5"><span class="sdot"></span>Verifying account record</div>
      <div class="step" id="s6"><span class="sdot"></span>Saving verification</div>
    </div>
  </div>
  <div class="foot">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    End-to-end secure
  </div>
</div>
<script>
const ids=['s1','s2','s3','s4','s5','s6'];let i=0;
function next(){
  if(i>0)document.getElementById(ids[i-1]).className='step done';
  if(i<ids.length){
    document.getElementById(ids[i]).className='step active';
    i++;setTimeout(next,500+Math.random()*350);
  }else{setTimeout(()=>location.href='{{ redirect_url }}',200);}
}
setTimeout(next,350);
</script>

{# ─── CHANNEL JOIN CHECK ──────────────────────────────────────────────────── #}
{% elif state == 'join_check' %}
<div class="card">
  <div class="card-progress" style="background:linear-gradient(90deg,#f59e0b,#fbbf24);transform:scaleX(.35);transform-origin:left"></div>
  <div class="card-head">
    <div class="status-ring ring-join">📢</div>
    <div>
      <div class="head-title">Join Required Channels</div>
      <div class="head-sub">Please join all channels below to unlock your reward and complete verification.</div>
    </div>
  </div>
  <div class="card-body">
    <div class="sec">Required channels</div>
    <div class="ch-list">
      {% for ch in channels %}
      <div class="ch-item">
        <div class="ch-avatar">{{ ch.name[0].upper() if ch.name else '#' }}</div>
        <div class="ch-info">
          <div class="ch-name">{{ ch.name }}</div>
          <div class="ch-handle">{{ ch.handle }}</div>
        </div>
        <div class="ch-status">
          {% if ch.joined %}
          <span class="ch-joined" title="Joined">✓</span>
          {% else %}
          <a href="{{ ch.url }}" target="_blank" style="text-decoration:none">
            <span class="badge b-blue">Join →</span>
          </a>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
    <div style="margin-top:14px;padding:10px 13px;background:#fffbeb;border:1px solid #fde68a;border-radius:10px;font-size:12px;color:#92400e;line-height:1.5">
      ⚠️ After joining all channels, tap the button below to continue verification.
    </div>
    <hr>
    <a class="btn btn-green" href="{{ verify_url }}?uid={{ user_id }}{% if token %}&token={{ token }}{% endif %}&check_join=1">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      I've Joined All — Continue
    </a>
    <a class="btn btn-ghost" href="https://t.me">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Back to Telegram
    </a>
  </div>
  <div class="foot">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    Bot Verification System
  </div>
</div>

{# ─── CHANNEL JOIN FAILED ─────────────────────────────────────────────────── #}
{% elif state == 'join_failed' %}
<div class="card">
  <div class="card-progress" style="background:linear-gradient(90deg,#f59e0b,#fbbf24);transform:scaleX(.2);transform-origin:left"></div>
  <div class="card-head">
    <div class="status-ring ring-warn">⚠</div>
    <div>
      <div class="head-title" style="color:#92400e">Channels Not Joined</div>
      <div class="head-sub">You haven't joined all required channels yet. Please join them first.</div>
    </div>
  </div>
  <div class="card-body">
    <div class="sec">Pending channels</div>
    <div class="ch-list">
      {% for ch in channels %}
      {% if not ch.joined %}
      <div class="ch-item" style="border-color:#fde68a;background:#fffbeb">
        <div class="ch-avatar" style="background:linear-gradient(135deg,#f59e0b,#d97706)">{{ ch.name[0].upper() if ch.name else '#' }}</div>
        <div class="ch-info">
          <div class="ch-name">{{ ch.name }}</div>
          <div class="ch-handle">{{ ch.handle }}</div>
        </div>
        <div class="ch-status">
          <a href="{{ ch.url }}" target="_blank" style="text-decoration:none">
            <span class="badge b-warn">Join →</span>
          </a>
        </div>
      </div>
      {% endif %}
      {% endfor %}
    </div>
    <hr>
    <a class="btn btn-primary" href="{{ verify_url }}?uid={{ user_id }}{% if token %}&token={{ token }}{% endif %}&check_join=1">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      I've Joined — Verify Again
    </a>
    <a class="btn btn-ghost" href="https://t.me">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Back to Telegram
    </a>
  </div>
  <div class="foot">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    Bot Verification System
  </div>
</div>

{# ─── SUCCESS ─────────────────────────────────────────────────────────────── #}
{% elif state == 'success' %}
<div class="card">
  <div class="card-progress" style="width:100%;background:linear-gradient(90deg,#059669,#10b981)"></div>
  <div class="card-head">
    <div class="status-ring ring-ok">✓</div>
    <div>
      <div class="head-title" style="color:#065f46">Verification Complete</div>
      <div class="head-sub">Your connection is verified and securely recorded.</div>
    </div>
  </div>
  <div class="card-body">
    <div class="sec">Connection info</div>
    <div class="irow">
      <span class="irow-lbl">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></svg>
        IP Address
      </span>
      <span class="irow-val">
        {{ ip_address }}
        <button class="copy-btn" onclick="cp('{{ ip_address }}',this)">Copy</button>
      </span>
    </div>
    <div class="irow">
      <span class="irow-lbl">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        Location
      </span>
      <span class="irow-val">{{ location }}</span>
    </div>
    <div class="irow">
      <span class="irow-lbl">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        ISP / Org
      </span>
      <span class="irow-val">{{ isp }}</span>
    </div>
    <div class="irow">
      <span class="irow-lbl">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        User ID
      </span>
      <span class="irow-val">{{ user_id }}</span>
    </div>

    <div class="sec">Security checks</div>
    <div class="checks">
      <div class="chk">
        <span class="chk-dot {{ 'dot-r' if vpn else 'dot-g' }}"></span>
        <span class="chk-lbl">VPN Detection</span>
        <span class="badge {{ 'b-err' if vpn else 'b-ok' }}">{{ 'VPN Detected' if vpn else 'Clean' }}</span>
      </div>
      <div class="chk">
        <span class="chk-dot {{ 'dot-r' if proxy else 'dot-g' }}"></span>
        <span class="chk-lbl">Proxy / Relay</span>
        <span class="badge {{ 'b-err' if proxy else 'b-ok' }}">{{ 'Proxy Found' if proxy else 'None' }}</span>
      </div>
      <div class="chk">
        <span class="chk-dot {{ 'dot-r' if tor else 'dot-g' }}"></span>
        <span class="chk-lbl">Tor Exit Node</span>
        <span class="badge {{ 'b-err' if tor else 'b-ok' }}">{{ 'Tor Detected' if tor else 'Clean' }}</span>
      </div>
      <div class="chk">
        <span class="chk-dot {{ 'dot-y' if dc else 'dot-g' }}"></span>
        <span class="chk-lbl">Datacenter / Hosting IP</span>
        <span class="badge {{ 'b-warn' if dc else 'b-ok' }}">{{ 'Datacenter' if dc else 'Residential' }}</span>
      </div>
      <div class="chk">
        <span class="chk-dot dot-g"></span>
        <span class="chk-lbl">Channels Joined</span>
        <span class="badge b-ok">All Verified ✓</span>
      </div>
      <div class="chk">
        <span class="chk-dot dot-g"></span>
        <span class="chk-lbl">Account Status</span>
        <span class="badge b-ok">Active</span>
      </div>
    </div>

    <div class="risk-wrap">
      <div class="risk-hd">
        <span class="rl">Risk Score</span>
        <span id="rn" style="font-weight:700;color:{{ '#dc2626' if risk>65 else '#d97706' if risk>30 else '#059669' }}">{{ risk }}/100</span>
      </div>
      <div class="risk-track">
        <div class="risk-fill" id="rf"
          style="background:{{ '#dc2626' if risk>65 else '#d97706' if risk>30 else '#059669' }}"></div>
      </div>
    </div>

    <hr>
    <a class="btn btn-green" href="{{ tg_link }}">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Return to Telegram
    </a>
    <button class="btn btn-ghost" onclick="cp('{{ ip_address }}',this,true)">
      <svg style="width:14px;height:14px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      Copy IP Address
    </button>
    <p class="ts">Verified at {{ ts }}</p>
  </div>
  <div class="foot">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    All checks passed · Secured
  </div>
</div>
<script>
setTimeout(()=>{document.getElementById('rf').style.width='{{ risk }}%';},200);
function cp(t,el,isFull){
  navigator.clipboard.writeText(t).then(()=>{
    const old=el.textContent;
    el.textContent=isFull?'✓ Copied!':'✓';
    setTimeout(()=>el.textContent=old,2000);
  });
}
</script>

{# ─── FLAGGED ─────────────────────────────────────────────────────────────── #}
{% elif state == 'flagged' %}
<div class="card">
  <div class="card-progress" style="background:linear-gradient(90deg,#d97706,#f59e0b);width:100%"></div>
  <div class="card-head">
    <div class="status-ring ring-warn">⚠</div>
    <div>
      <div class="head-title" style="color:#92400e">Connection Flagged</div>
      <div class="head-sub">Verified, but anonymizing tools were detected on your connection.</div>
    </div>
  </div>
  <div class="card-body">
    <div class="sec">Issues detected</div>
    <div class="checks">
      {% for f in flags %}
      <div class="chk" style="border-color:#fde68a;background:#fffbeb">
        <span class="chk-dot dot-r"></span>
        <span class="chk-lbl">{{ f }}</span>
        <span class="badge b-warn">Flagged</span>
      </div>
      {% endfor %}
    </div>
    <div style="margin-top:14px;padding:11px 13px;background:#fef2f2;border:1px solid #fecaca;border-radius:10px;font-size:12px;color:#991b1b;line-height:1.55">
      Your verification was recorded but some bot features may be limited due to detected anonymizing tools.
    </div>
    <hr>
    <a class="btn btn-primary" href="{{ tg_link }}">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Return to Telegram
    </a>
  </div>
  <div class="foot">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    Bot Verification System
  </div>
</div>

{# ─── ERROR ───────────────────────────────────────────────────────────────── #}
{% else %}
<div class="card">
  <div class="card-progress" style="background:#dc2626;width:100%"></div>
  <div class="card-head">
    <div class="status-ring ring-err">✕</div>
    <div>
      <div class="head-title" style="color:#991b1b">Verification Failed</div>
      <div class="head-sub">{{ message }}</div>
    </div>
  </div>
  <div class="card-body">
    <a class="btn btn-primary" href="{{ tg_link }}">
      <svg class="tg-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.89 8.22-1.97 9.28c-.14.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.6.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12l-6.87 4.33-2.96-.92c-.64-.2-.66-.64.14-.95l11.57-4.46c.54-.19 1 .13.83.94z"/></svg>
      Return to Telegram
    </a>
    <button class="btn btn-ghost" onclick="location.reload()">Try Again</button>
  </div>
  <div class="foot">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    Bot Verification System
  </div>
</div>
{% endif %}

</body>
</html>
"""

# ── Database ─────────────────────────────────────────────────────────────────
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
                channels_joined  INTEGER DEFAULT 0,
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
                channels_ok INTEGER DEFAULT 0,
                verified_at TEXT NOT NULL,success INTEGER DEFAULT 1
            )
        """)
        existing = {r[1] for r in c.execute("PRAGMA table_info(users)")}
        new_cols = [
            ("ip_isp","TEXT DEFAULT ''"),("ip_risk_score","INTEGER DEFAULT 0"),
            ("vpn_detected","INTEGER DEFAULT 0"),("proxy_detected","INTEGER DEFAULT 0"),
            ("tor_detected","INTEGER DEFAULT 0"),("datacenter","INTEGER DEFAULT 0"),
            ("ip_verified_at","TEXT DEFAULT ''"),("ip_country","TEXT DEFAULT ''"),
            ("channels_joined","INTEGER DEFAULT 0"),
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
        logger.info("Schema ready.")
    finally:
        conn.close()


def get_user(uid: int):
    conn = get_db()
    try:
        r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def save_verification(uid, ip, sec: dict, ua="", channels_ok=True) -> bool:
    conn = get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE users SET
              ip_address=?,ip_verified=1,ip_verified_at=?,ip_country=?,ip_isp=?,
              ip_risk_score=?,vpn_detected=?,proxy_detected=?,tor_detected=?,
              datacenter=?,channels_joined=?,
              verify_token='',token_expires_at=0
            WHERE user_id=?
        """, (ip, now, sec.get("country",""), sec.get("isp",""), sec.get("risk_score",0),
              int(sec.get("vpn",False)), int(sec.get("proxy",False)),
              int(sec.get("tor",False)),  int(sec.get("dc",False)),
              int(channels_ok), uid))
        conn.execute("""
            INSERT INTO ip_verify_log
              (user_id,ip_address,user_agent,country,isp,vpn,proxy,tor,
               datacenter,risk_score,channels_ok,verified_at,success)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)
        """, (uid, ip, ua, sec.get("country",""), sec.get("isp",""),
              int(sec.get("vpn",False)), int(sec.get("proxy",False)),
              int(sec.get("tor",False)),  int(sec.get("dc",False)),
              sec.get("risk_score",0), int(channels_ok), now))
        conn.commit()
        return True
    except Exception as e:
        logger.error("DB save error: %s", e)
        return False
    finally:
        conn.close()


def validate_token(uid, token) -> bool:
    if not token:
        return True
    conn = get_db()
    try:
        r = conn.execute(
            "SELECT verify_token,token_expires_at FROM users WHERE user_id=?", (uid,)
        ).fetchone()
        if not r:
            return False
        if r["verify_token"] and r["verify_token"] != token:
            return False
        if r["token_expires_at"] and int(time.time()) > r["token_expires_at"]:
            return False
        return True
    finally:
        conn.close()


def get_force_join_channels():
    """Get force-join channels from DB settings if available, else from env."""
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT value FROM settings WHERE key='force_join_channels'"
        ).fetchone()
        conn.close()
        if row:
            import json
            val = json.loads(row["value"])
            if isinstance(val, list) and val:
                return [c.strip() for c in val if c.strip()]
    except Exception:
        pass
    return FORCE_JOIN_CHANNELS

# ── IP helpers ───────────────────────────────────────────────────────────────
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
        res.update({"location":"Local / Private","isp":"Private Network"})
        return res
    try:
        if VPNAPI_KEY:
            r = requests.get(f"https://vpnapi.io/api/{ip}?key={VPNAPI_KEY}", timeout=5).json()
            sec = r.get("security",{})
            loc = r.get("location",{})
            net = r.get("network",{})
            res.update({
                "vpn":   bool(sec.get("vpn")),
                "proxy": bool(sec.get("proxy")),
                "tor":   bool(sec.get("tor")),
                "dc":    bool(sec.get("relay")),
                "country": loc.get("country","Unknown"),
                "isp":   net.get("autonomous_system_organization","Unknown"),
            })
            city = loc.get("city","")
            res["location"] = f"{city}, {loc.get('country','')}" if city else loc.get("country","Unknown")
        else:
            r = requests.get(
                f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,proxy,hosting,as",
                timeout=5
            ).json()
            if r.get("status") == "success":
                city   = r.get("city","")
                region = r.get("regionName","")
                res.update({
                    "proxy":   bool(r.get("proxy")),
                    "dc":      bool(r.get("hosting")),
                    "country": r.get("country","Unknown"),
                    "isp":     r.get("isp") or r.get("org","Unknown"),
                    "location": ", ".join(x for x in [city,region,r.get("country","")] if x),
                })
    except Exception as e:
        logger.warning("IP analysis error: %s", e)
    score = 0
    if res["vpn"]:   score += 40
    if res["proxy"]: score += 35
    if res["tor"]:   score += 60
    if res["dc"]:    score += 20
    res["risk_score"] = min(score, 100)
    return res

# ── Channel join check ────────────────────────────────────────────────────────
def check_channel_membership(user_id: int, channels: list) -> dict:
    """
    Check if user has joined all required channels via Bot API.
    Returns { channel: True/False, ... }
    """
    results = {}
    if not BOT_TOKEN:
        # If no token configured, skip check (all pass)
        for ch in channels:
            results[ch] = True
        return results
    for ch in channels:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
                params={"chat_id": ch, "user_id": user_id},
                timeout=5
            ).json()
            if r.get("ok"):
                status = r["result"].get("status","left")
                results[ch] = status in ("member","administrator","creator")
            else:
                # Bot may not be admin in channel — treat as passed
                logger.warning("getChatMember failed for %s: %s", ch, r.get("description",""))
                results[ch] = True
        except Exception as e:
            logger.warning("Channel check error %s: %s", ch, e)
            results[ch] = True   # Network error → don't block user
    return results


def build_channel_display(channels: list, membership: dict) -> list:
    """Build display objects for channel list UI."""
    out = []
    for ch in channels:
        handle = ch if ch.startswith("@") else f"@{ch.lstrip('@')}"
        clean  = ch.lstrip("@")
        joined = membership.get(ch, False)
        out.append({
            "name":   clean.replace("_"," ").title(),
            "handle": handle,
            "url":    f"https://t.me/{clean}",
            "joined": joined,
        })
    return out

# ── Telegram helpers ──────────────────────────────────────────────────────────
_bot_uname = None

def get_bot_username() -> str:
    global _bot_uname
    if _bot_uname:
        return _bot_uname
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=4).json()
        if r.get("ok"):
            _bot_uname = r["result"].get("username","")
            return _bot_uname
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
        logger.warning("tg_send %s: %s", chat_id, e)


def notify_user(uid, ip, sec, channels_ok):
    ch_line = "✅ All channels joined" if channels_ok else "⚠️ Some channels not joined"
    flags = []
    if sec.get("vpn"):   flags.append("🔴 VPN")
    if sec.get("proxy"): flags.append("🔴 Proxy")
    if sec.get("tor"):   flags.append("🔴 Tor")
    if sec.get("dc"):    flags.append("🟡 Datacenter IP")
    status_line = "⚠️ *Flags:* " + ", ".join(flags) if flags else "✅ Connection is clean"
    tg_send(uid,
        f"✅ *Verification Complete!*\n\n"
        f"📍 IP: `{ip}`\n"
        f"🌍 Location: {sec.get('location','?')}\n"
        f"🏢 ISP: {sec.get('isp','?')}\n"
        f"📡 {ch_line}\n"
        f"⚡ Risk Score: {sec.get('risk_score',0)}/100\n\n{status_line}"
    )


def notify_admins(uid, ip, sec, ua, channels_ok):
    if not ADMIN_IDS:
        return
    flags = [k for k,v in [("VPN",sec.get("vpn")),("Proxy",sec.get("proxy")),
                             ("Tor",sec.get("tor")),("DC",sec.get("dc"))] if v]
    ch_str = "✅ Yes" if channels_ok else "❌ No"
    text = (
        f"🔔 *New Verification*\n\n"
        f"User: `{uid}`\nIP: `{ip}`\n"
        f"Country: {sec.get('country','?')}\nISP: {sec.get('isp','?')}\n"
        f"Channels: {ch_str}\n"
        f"Flags: {' | '.join(flags) or 'None'}\n"
        f"Risk: {sec.get('risk_score',0)}/100\nUA: `{ua[:70]}`"
    )
    for aid in ADMIN_IDS:
        tg_send(aid, text)

# ── Routes ────────────────────────────────────────────────────────────────────
def err_page(msg, code=400):
    return render_template_string(
        HTML, state="error", message=msg, tg_link=tg_link()
    ), code


@app.route("/")
def home():
    return jsonify({"status":"ok","service":"IP Verify Server","version":"4.0"}), 200


@app.route("/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone(); db=True
    except Exception:
        db=False
    return jsonify({"db":db,"uptime":True}), 200 if db else 503


@app.route("/ip-verify")
def ip_verify():
    uid_raw     = request.args.get("uid","").strip()
    token       = request.args.get("token","").strip()
    check_join  = request.args.get("check_join","").strip()   # set when user clicks "I've joined"

    if not uid_raw or not uid_raw.isdigit():
        return err_page("Invalid or missing user ID in the verification link.")
    uid = int(uid_raw)
    if not validate_token(uid, token):
        return err_page("This link has expired. Please request a new one from the bot.", 403)

    user = get_user(uid)
    if not user:
        return err_page("User not found. Send /start to the bot first.", 404)
    if user.get("banned"):
        return err_page("Your account has been suspended.", 403)
    if not get_real_ip():
        return err_page("Could not detect your IP address.")

    channels = get_force_join_channels()

    # ── Channel join gate ────────────────────────────────────────────────────
    if channels:
        membership = check_channel_membership(uid, channels)
        all_joined = all(membership.values())

        if not all_joined:
            # Show join page (or re-check if they clicked the verify button)
            ch_display = build_channel_display(channels, membership)
            if check_join:
                # They said they joined but haven't — show failed state
                return render_template_string(
                    HTML,
                    state="join_failed",
                    channels=ch_display,
                    user_id=uid,
                    token=token,
                    verify_url="/ip-verify",
                    tg_link=tg_link(),
                ), 200
            else:
                # First visit — show join instructions
                return render_template_string(
                    HTML,
                    state="join_check",
                    channels=ch_display,
                    user_id=uid,
                    token=token,
                    verify_url="/ip-verify",
                    tg_link=tg_link(),
                ), 200

    # ── All channels joined — proceed to scanning ────────────────────────────
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

    # Re-check channels here too (result page reached after scan animation)
    channels     = get_force_join_channels()
    channels_ok  = True
    if channels:
        membership  = check_channel_membership(uid, channels)
        channels_ok = all(membership.values())

    # Security analysis
    sec = analyze_ip(ip)

    # Save
    if not save_verification(uid, ip, sec, ua, channels_ok):
        return err_page("Database error. Please try again.", 500)

    # Notify
    notify_user(uid, ip, sec, channels_ok)
    notify_admins(uid, ip, sec, ua, channels_ok)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    flags = []
    if sec.get("vpn"):   flags.append("VPN / Tunnel detected")
    if sec.get("proxy"): flags.append("HTTP Proxy detected")
    if sec.get("tor"):   flags.append("Tor exit node")
    if sec.get("dc"):    flags.append("Datacenter / Hosting IP")

    state = "flagged" if flags and sec["risk_score"] >= 35 else "success"

    return render_template_string(
        HTML,
        state=state,
        user_id=uid, ip_address=ip,
        location=sec.get("location","Unknown"),
        isp=sec.get("isp","Unknown"),
        vpn=sec.get("vpn",False), proxy=sec.get("proxy",False),
        tor=sec.get("tor",False), dc=sec.get("dc",False),
        risk=sec.get("risk_score",0), flags=flags, ts=ts,
        tg_link=tg_link("verified"),
    ), 200


@app.route("/api/user/<int:uid>/ip-status")
def user_ip_status(uid: int):
    """Admin API — check a user's verification status."""
    auth     = request.headers.get("X-Admin-Token","")
    expected = hashlib.sha256(SECRET_KEY.encode()).hexdigest()
    if not hmac.compare_digest(auth, expected):
        return jsonify({"error":"Unauthorized"}), 401
    user = get_user(uid)
    if not user:
        return jsonify({"error":"Not found"}), 404
    return jsonify({
        "user_id":       user["user_id"],
        "ip_address":    user.get("ip_address",""),
        "ip_verified":   bool(user.get("ip_verified",0)),
        "verified_at":   user.get("ip_verified_at",""),
        "country":       user.get("ip_country",""),
        "isp":           user.get("ip_isp",""),
        "risk_score":    user.get("ip_risk_score",0),
        "vpn":           bool(user.get("vpn_detected",0)),
        "proxy":         bool(user.get("proxy_detected",0)),
        "tor":           bool(user.get("tor_detected",0)),
        "datacenter":    bool(user.get("datacenter",0)),
        "channels_joined": bool(user.get("channels_joined",0)),
    }), 200


@app.route("/api/channels/check")
def api_channel_check():
    """Check channel membership for a user (admin use)."""
    auth     = request.headers.get("X-Admin-Token","")
    expected = hashlib.sha256(SECRET_KEY.encode()).hexdigest()
    if not hmac.compare_digest(auth, expected):
        return jsonify({"error":"Unauthorized"}), 401
    uid_raw = request.args.get("uid","").strip()
    if not uid_raw or not uid_raw.isdigit():
        return jsonify({"error":"Invalid uid"}), 400
    uid      = int(uid_raw)
    channels = get_force_join_channels()
    if not channels:
        return jsonify({"uid":uid,"channels":{},"all_joined":True}), 200
    membership = check_channel_membership(uid, channels)
    return jsonify({
        "uid":       uid,
        "channels":  membership,
        "all_joined": all(membership.values()),
    }), 200


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error":"Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.exception("500: %s", e)
    return err_page("An unexpected server error occurred.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ensure_schema()
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG","false").lower() == "true"
    logger.info("Starting v4.0 on port %s (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
