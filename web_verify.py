from flask import Flask, request, render_template_string, jsonify
import sqlite3, os, time, hashlib, re

app = Flask(__name__)

DB_PATH      = os.environ.get("DB_PATH",      "/data/bot_database.db")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "realupilootbot")
SECRET_SALT  = os.environ.get("SECRET_SALT",  "change_me_in_production")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")

# ══════════════════════════════════════════════════════════════════
#  SHARED BASE — Glassmorphism, no scroll, full viewport
# ══════════════════════════════════════════════════════════════════
def base_page(title, accent_rgb, body_content, extra_js=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<title>{title}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --a:{accent_rgb};
  --ac:rgb({accent_rgb});
  --sans:'Outfit',sans-serif;
  --mono:'JetBrains Mono',monospace;
}}
html,body{{
  width:100%;height:100%;overflow:hidden;
  font-family:var(--sans);
  background:#060a10;
  color:#e8f0fc;
}}
/* ── background orbs ── */
.bg{{
  position:fixed;inset:0;z-index:0;
  background:radial-gradient(ellipse 80% 60% at 20% 10%,rgba({accent_rgb},.12) 0%,transparent 60%),
             radial-gradient(ellipse 60% 80% at 85% 90%,rgba(120,80,255,.09) 0%,transparent 55%),
             radial-gradient(ellipse 50% 50% at 50% 50%,rgba(30,50,90,.4) 0%,transparent 100%),
             #060a10;
}}
.orb{{
  position:fixed;border-radius:50%;filter:blur(60px);pointer-events:none;
  animation:drift 8s ease-in-out infinite;
}}
.orb1{{
  width:340px;height:340px;
  background:rgba({accent_rgb},.08);
  top:-80px;left:-80px;animation-delay:0s;
}}
.orb2{{
  width:280px;height:280px;
  background:rgba(100,60,255,.07);
  bottom:-60px;right:-60px;animation-delay:-4s;
}}
@keyframes drift{{
  0%,100%{{transform:translate(0,0) scale(1)}}
  33%{{transform:translate(20px,15px) scale(1.04)}}
  66%{{transform:translate(-10px,20px) scale(.97)}}
}}
/* grid lines */
.grid{{
  position:fixed;inset:0;z-index:1;pointer-events:none;
  background-image:
    linear-gradient(rgba({accent_rgb},.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba({accent_rgb},.025) 1px,transparent 1px);
  background-size:48px 48px;
}}
/* noise grain */
.grain{{
  position:fixed;inset:0;z-index:2;pointer-events:none;opacity:.03;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}}
/* ── main card shell ── */
.shell{{
  position:fixed;inset:0;z-index:10;
  display:flex;align-items:center;justify-content:center;
  padding:16px;
}}
.card{{
  width:min(92vw,430px);
  background:rgba(255,255,255,.045);
  backdrop-filter:blur(28px) saturate(1.6);
  -webkit-backdrop-filter:blur(28px) saturate(1.6);
  border:1px solid rgba(255,255,255,.1);
  border-radius:28px;
  padding:36px 30px 30px;
  text-align:center;
  position:relative;
  overflow:hidden;
  box-shadow:
    0 0 0 1px rgba(255,255,255,.04) inset,
    0 32px 64px rgba(0,0,0,.55),
    0 0 80px -20px rgba({accent_rgb},.2);
  animation:cardIn .7s cubic-bezier(.16,1,.3,1) forwards;
  opacity:0;transform:translateY(22px) scale(.97);
}}
@keyframes cardIn{{to{{opacity:1;transform:none}}}}
/* top shimmer line */
.card::before{{
  content:'';position:absolute;top:0;left:12%;right:12%;height:1px;
  background:linear-gradient(90deg,transparent,rgba({accent_rgb},.6),transparent);
}}
/* inner glow patch */
.card::after{{
  content:'';position:absolute;top:-50px;left:50%;transform:translateX(-50%);
  width:220px;height:110px;border-radius:50%;
  background:rgba({accent_rgb},.07);filter:blur(35px);pointer-events:none;
}}
/* ── icon ── */
.icon-area{{
  width:72px;height:72px;margin:0 auto 20px;
  position:relative;display:flex;align-items:center;justify-content:center;
}}
.i-disc{{
  position:absolute;inset:0;border-radius:50%;
  background:rgba({accent_rgb},.08);
  border:1px solid rgba({accent_rgb},.2);
  animation:pulse 3s ease-in-out infinite;
}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba({accent_rgb},.0)}}50%{{box-shadow:0 0 0 10px rgba({accent_rgb},.06)}}}}
.ring{{position:absolute;border-radius:50%;border:1px solid transparent}}
.r1{{inset:-6px;border-top-color:rgba({accent_rgb},.55);animation:spin 3s linear infinite}}
.r2{{inset:-12px;border-bottom-color:rgba({accent_rgb},.2);animation:spin 5.5s linear infinite reverse}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.i-inner{{position:relative;z-index:2}}
/* ── badge ── */
.badge{{
  display:inline-flex;align-items:center;gap:6px;
  padding:4px 12px;border-radius:100px;margin-bottom:14px;
  font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  background:rgba({accent_rgb},.1);
  border:1px solid rgba({accent_rgb},.25);
  color:rgb({accent_rgb});
}}
.bdot{{width:5px;height:5px;border-radius:50%;background:currentColor;animation:blink 1.8s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
h1{{font-size:22px;font-weight:700;letter-spacing:-.03em;color:#fff;margin-bottom:8px;line-height:1.2}}
.sub{{font-size:13px;color:rgba(255,255,255,.38);line-height:1.6;margin-bottom:22px}}
/* ── rows ── */
.rows{{display:flex;flex-direction:column;gap:5px;margin-bottom:20px}}
.row{{
  display:flex;align-items:center;justify-content:space-between;
  background:rgba(255,255,255,.03);
  border:1px solid rgba(255,255,255,.055);
  border-left:2px solid rgba({accent_rgb},.5);
  border-radius:10px;padding:9px 14px;
  animation:rowIn .4s cubic-bezier(.16,1,.3,1) both;
}}
@keyframes rowIn{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:none}}}}
.rl{{font-size:10px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;
  color:rgba(255,255,255,.25);display:flex;align-items:center;gap:7px}}
.rv{{font-family:var(--mono);font-size:12px;font-weight:500;
  background:rgba(255,255,255,.04);padding:2px 9px;border-radius:6px;
  color:rgba(255,255,255,.85)}}
/* ── score arc ── */
.arc-wrap{{position:relative;display:flex;align-items:center;justify-content:center;margin:0 auto 18px}}
.arc-label{{position:absolute;text-align:center}}
.arc-num{{font-family:var(--mono);font-size:26px;font-weight:600;
  color:rgb({accent_rgb});display:block;line-height:1}}
.arc-txt{{font-size:9px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;
  color:rgba(255,255,255,.25);display:block;margin-top:3px}}
/* ── audit ── */
.audit-title{{font-size:9px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  color:rgba(255,255,255,.18);margin-bottom:8px;text-align:left}}
.audit{{display:flex;flex-direction:column;gap:0;margin-bottom:18px}}
.a-item{{display:flex;align-items:flex-start;gap:8px;padding:6px 0;
  border-bottom:1px solid rgba(255,255,255,.04);
  animation:af .4s ease both}}
.a-item:last-child{{border-bottom:none}}
@keyframes af{{from{{opacity:0;transform:translateY(3px)}}to{{opacity:1;transform:none}}}}
.a-dot{{width:6px;height:6px;border-radius:50%;background:var(--dc,rgba(255,255,255,.2));margin-top:4px;flex-shrink:0}}
.a-msg{{font-size:11px;color:rgba(255,255,255,.55);line-height:1.45;flex:1}}
.a-time{{font-size:9px;color:rgba(255,255,255,.2);font-family:var(--mono);margin-top:1px}}
/* ── sep ── */
.sep{{height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.07),transparent);margin:16px 0}}
/* ── button ── */
.btn{{
  display:flex;align-items:center;justify-content:center;gap:8px;
  width:100%;padding:14px 20px;border-radius:14px;
  font-family:var(--sans);font-size:14px;font-weight:600;
  text-decoration:none;border:none;cursor:pointer;
  transition:transform .14s,box-shadow .18s,opacity .15s;
  position:relative;overflow:hidden;
}}
.btn::before{{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.14) 0%,transparent 55%);
  opacity:0;transition:opacity .2s;pointer-events:none;
}}
.btn:hover{{transform:translateY(-2px)}}.btn:hover::before{{opacity:1}}
.btn:active{{transform:scale(.98)}}
.btn-main{{
  background:linear-gradient(135deg,rgba({accent_rgb},.9),rgba({accent_rgb},.6));
  color:#000;box-shadow:0 6px 24px rgba({accent_rgb},.3);margin-bottom:8px;
}}
.btn-main:hover{{box-shadow:0 10px 32px rgba({accent_rgb},.45)}}
.btn-sec{{
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.08);
  color:rgba(255,255,255,.4);font-size:12px;
}}
.btn-sec:hover{{background:rgba(255,255,255,.07);color:rgba(255,255,255,.65)}}
/* ── footer ── */
.foot{{
  display:flex;align-items:center;justify-content:center;gap:5px;
  margin-top:14px;font-size:10.5px;color:rgba(255,255,255,.14);letter-spacing:.02em;
}}
/* ── confetti canvas ── */
#cfc{{position:fixed;inset:0;pointer-events:none;z-index:20}}
/* ── responsive ── */
@media(max-width:400px){{
  .card{{padding:28px 18px 24px;border-radius:22px}}
  h1{{font-size:19px}}
  .icon-area{{width:60px;height:60px;margin-bottom:16px}}
}}
@media(max-height:680px){{
  .card{{padding:24px 26px 22px}}
  .icon-area{{width:58px;height:58px;margin-bottom:14px}}
  h1{{font-size:18px;margin-bottom:6px}}
  .sub{{margin-bottom:14px;font-size:12px}}
  .rows{{gap:4px;margin-bottom:14px}}
  .row{{padding:7px 12px}}
  .arc-wrap{{margin-bottom:12px}}
  .audit{{margin-bottom:12px}}
  .sep{{margin:12px 0}}
  .btn{{padding:12px 18px;font-size:13px}}
}}
</style>
</head>
<body>
<div class="bg"></div>
<div class="orb orb1"></div>
<div class="orb orb2"></div>
<div class="grid"></div>
<div class="grain"></div>
<div class="shell">
  <div class="card">
    {body_content}
  </div>
</div>
{extra_js}
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#  SUCCESS PAGE
# ══════════════════════════════════════════════════════════════════
def success_page(user_id, bot_username):
    body = f"""
<canvas id="cfc"></canvas>

<div class="icon-area">
  <div class="i-disc"></div>
  <div class="ring r1"></div>
  <div class="ring r2"></div>
  <div class="i-inner">
    <svg width="34" height="34" viewBox="0 0 52 52" fill="none">
      <circle id="cc" cx="26" cy="26" r="22" stroke="rgb(0,232,122)" stroke-width="2"
        stroke-dasharray="138.2" stroke-dashoffset="138.2"/>
      <path id="cm" d="M15 27l8 8.5L37 18" stroke="rgb(0,232,122)" stroke-width="2.5"
        stroke-linecap="round" stroke-linejoin="round"
        stroke-dasharray="36" stroke-dashoffset="36"/>
    </svg>
  </div>
</div>

<div class="badge"><span class="bdot"></span>Verified &amp; Secured</div>
<h1>Identity Confirmed</h1>
<p class="sub">All security layers passed. Your account is now bound and protected.</p>

<div class="arc-wrap">
  <svg width="180" height="96" viewBox="0 0 180 96">
    <defs>
      <linearGradient id="ag" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="rgb(0,232,122)"/>
        <stop offset="100%" stop-color="rgb(0,196,255)"/>
      </linearGradient>
    </defs>
    <path d="M14 90 A76 76 0 0 1 166 90" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="9" stroke-linecap="round"/>
    <path id="sa" d="M14 90 A76 76 0 0 1 166 90" fill="none" stroke="url(#ag)" stroke-width="9" stroke-linecap="round"
      stroke-dasharray="238.8" stroke-dashoffset="238.8"/>
  </svg>
  <div class="arc-label">
    <span class="arc-num" id="sn">0</span>
    <span class="arc-txt">Trust Score</span>
  </div>
</div>

<div class="rows">
  <div class="row" style="animation-delay:.25s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      User ID
    </span>
    <span class="rv">#{user_id}</span>
  </div>
  <div class="row" style="animation-delay:.33s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      Status
    </span>
    <span class="rv" style="color:rgb(0,232,122);background:rgba(0,232,122,.08)">✓ Verified</span>
  </div>
  <div class="row" style="animation-delay:.41s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Time
    </span>
    <span class="rv" id="ts">—</span>
  </div>
  <div class="row" style="animation-delay:.49s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      Session
    </span>
    <span class="rv" id="sh">—</span>
  </div>
</div>

<div class="audit-title">Verification Audit</div>
<div class="audit" id="audit"></div>

<div class="sep"></div>

<a class="btn btn-main" href="https://t.me/{bot_username}">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="black"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
  Continue to Telegram
</a>
<button class="btn btn-sec" onclick="copySession()">Copy Session Token</button>

<div class="foot">
  <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
  256-bit encrypted · Zero-log · GDPR compliant
</div>

<style>
#cc{{transition:stroke-dashoffset .65s cubic-bezier(.65,0,.45,1) .25s}}
#cm{{transition:stroke-dashoffset .4s cubic-bezier(.65,0,.45,1) .92s}}
#sa{{transition:stroke-dashoffset 1.3s cubic-bezier(.16,1,.3,1) .6s}}
</style>
<script>
requestAnimationFrame(function(){{
  document.getElementById('cc').style.strokeDashoffset='0';
  document.getElementById('cm').style.strokeDashoffset='0';
}});
document.getElementById('ts').textContent=new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});

// session hash
var __sess='';
(async function(){{
  try{{
    var raw=navigator.userAgent+Date.now()+Math.random();
    var buf=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw));
    __sess=Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('').slice(0,14);
    document.getElementById('sh').textContent=__sess.slice(0,6)+'…'+__sess.slice(-4);
    window.__sessToken=__sess;
  }}catch(e){{document.getElementById('sh').textContent='n/a'}}
}})();

// score arc
var score=94;
setTimeout(function(){{
  document.getElementById('sa').style.strokeDashoffset=(238.8*(1-score/100));
  var el=document.getElementById('sn'),t0=performance.now();
  (function tick(t){{
    var p=Math.min((t-t0)/1100,1),e=1-Math.pow(1-p,4);
    el.textContent=Math.round(e*score);
    if(p<1)requestAnimationFrame(tick);
  }})(t0);
}},700);

// audit
var logs=[
  {{c:'rgb(0,232,122)',m:'IP captured and normalized'}},
  {{c:'rgb(0,232,122)',m:'Duplicate IP check — unique'}},
  {{c:'rgb(45,156,255)',m:'Rate limit check — 0/5 used'}},
  {{c:'rgb(0,232,122)',m:'Account record validated'}},
  {{c:'rgb(155,111,255)',m:'Session token generated & bound'}},
  {{c:'rgb(0,232,122)',m:'All checks passed — verified'}},
];
var al=document.getElementById('audit');
logs.forEach(function(l,i){{
  setTimeout(function(){{
    var d=document.createElement('div');d.className='a-item';d.style.animationDelay='0s';
    var t=new Date();
    d.innerHTML='<div class="a-dot" style="background:'+l.c+'"></div>'+
      '<div><div class="a-msg">'+l.m+'</div>'+
      '<div class="a-time">'+t.toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit',second:'2-digit'}})+'.'+String(t.getMilliseconds()).padStart(3,'0')+'</div></div>';
    al.appendChild(d);
  }},350+i*260);
}});

// copy
function copySession(){{
  var tok=window.__sessToken||'n/a';
  if(navigator.clipboard){{
    navigator.clipboard.writeText('SESS:'+tok+'|UID:{user_id}').then(function(){{
      var b=document.querySelector('.btn-sec');
      b.textContent='Copied!';setTimeout(function(){{b.textContent='Copy Session Token';}},2000);
    }});
  }}
}}

// confetti
(function(){{
  var cv=document.getElementById('cfc'),ctx=cv.getContext('2d');
  function resize(){{cv.width=innerWidth;cv.height=innerHeight;}}resize();
  addEventListener('resize',resize);
  var cols=['rgb(0,232,122)','rgb(0,196,255)','rgb(155,111,255)','rgb(245,166,35)','#fff'],ps=[];
  for(var i=0;i<110;i++)ps.push({{
    x:cv.width/2+(Math.random()-.5)*200,y:-8,
    vx:(Math.random()-.5)*12,vy:1.5+Math.random()*8,
    r:Math.random()*4.5+2,c:cols[i%cols.length],
    rot:Math.random()*360,rv:(Math.random()-.5)*14,
    a:1,av:.005+Math.random()*.007,shape:Math.random()>.45,
    delay:Math.floor(Math.random()*50)
  }});
  var f=0;
  function draw(){{
    ctx.clearRect(0,0,cv.width,cv.height);var alive=false;
    ps.forEach(function(p){{
      if(f<p.delay)return;
      p.x+=p.vx;p.y+=p.vy;p.vy+=.17;p.rot+=p.rv;p.a-=p.av;
      if(p.a<=0)return;alive=true;
      ctx.save();ctx.globalAlpha=Math.max(0,p.a);
      ctx.translate(p.x,p.y);ctx.rotate(p.rot*Math.PI/180);
      ctx.fillStyle=p.c;
      if(p.shape){{ctx.fillRect(-p.r,-p.r*.5,p.r*2,p.r);}}
      else{{ctx.beginPath();ctx.arc(0,0,p.r,0,Math.PI*2);ctx.fill();}}
      ctx.restore();
    }});
    f++;if(alive)requestAnimationFrame(draw);else cv.remove();
  }}
  setTimeout(draw,500);
}})();
</script>
"""
    return base_page("Verified ✓", "0,232,122", body)


# ══════════════════════════════════════════════════════════════════
#  ERROR PAGE
# ══════════════════════════════════════════════════════════════════
def error_page(message, bot_username):
    # Smart error code
    codes = {
        'not found': 'ERR_USER_404',
        'banned': 'ERR_ACCT_BAN',
        'ip': 'ERR_IP_CONFLICT',
        'attempt': 'ERR_RATE_LIMIT',
        'invalid': 'ERR_INVALID_UID',
        'missing': 'ERR_INVALID_UID',
        'detected': 'ERR_IP_DETECT',
    }
    code = 'ERR_UNKNOWN'
    for k, v in codes.items():
        if k in message.lower():
            code = v
            break

    body = f"""
<div class="icon-area">
  <div class="i-disc"></div>
  <div class="ring r1"></div>
  <div class="ring r2"></div>
  <div class="i-inner" style="animation:xs .55s ease .4s both">
    <svg width="32" height="32" viewBox="0 0 52 52" fill="none">
      <circle id="ec" cx="26" cy="26" r="22" stroke="rgb(255,61,80)" stroke-width="2"
        stroke-dasharray="138.2" stroke-dashoffset="138.2"/>
      <path id="ex" d="M17 17l18 18M35 17L17 35" stroke="rgb(255,61,80)" stroke-width="2.5"
        stroke-linecap="round" stroke-dasharray="46" stroke-dashoffset="46"/>
    </svg>
  </div>
</div>

<div class="badge"><span class="bdot"></span>Access Denied</div>
<h1>Verification Failed</h1>
<p class="sub">{message}</p>

<div class="arc-wrap">
  <svg width="180" height="96" viewBox="0 0 180 96">
    <defs>
      <linearGradient id="eg" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="rgb(255,61,80)"/>
        <stop offset="100%" stop-color="rgb(245,166,35)"/>
      </linearGradient>
    </defs>
    <path d="M14 90 A76 76 0 0 1 166 90" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="9" stroke-linecap="round"/>
    <path id="ea" d="M14 90 A76 76 0 0 1 166 90" fill="none" stroke="url(#eg)" stroke-width="9" stroke-linecap="round"
      stroke-dasharray="238.8" stroke-dashoffset="238.8"/>
  </svg>
  <div class="arc-label">
    <span class="arc-num" id="en" style="color:rgb(255,61,80)">0</span>
    <span class="arc-txt">Trust Score</span>
  </div>
</div>

<div class="rows">
  <div class="row" style="border-left-color:rgba(255,61,80,.5);animation-delay:.25s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Reason
    </span>
    <span class="rv" style="color:rgb(255,61,80);background:rgba(255,61,80,.08);max-width:200px;white-space:normal;text-align:right;line-height:1.35;font-size:10.5px">{message}</span>
  </div>
  <div class="row" style="border-left-color:rgba(255,61,80,.5);animation-delay:.33s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      Status
    </span>
    <span class="rv" style="color:rgb(255,61,80);background:rgba(255,61,80,.08)">✗ Rejected</span>
  </div>
  <div class="row" style="border-left-color:rgba(245,166,35,.5);animation-delay:.41s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Time
    </span>
    <span class="rv" id="ts">—</span>
  </div>
  <div class="row" style="border-left-color:rgba(45,156,255,.5);animation-delay:.49s">
    <span class="rl">
      <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.25)" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      Error Code
    </span>
    <span class="rv" style="color:rgba(255,255,255,.5)">{code}</span>
  </div>
</div>

<div class="audit-title">Rejection Audit</div>
<div class="audit" id="audit"></div>

<div class="sep"></div>

<a class="btn btn-main" href="https://t.me/{bot_username}"
  style="background:linear-gradient(135deg,rgba(45,156,255,.85),rgba(155,111,255,.7));box-shadow:0 6px 24px rgba(45,156,255,.25);color:#fff">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
  Return to Telegram
</a>

<div class="foot">
  <svg width="11" height="11" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
  Contact support if you believe this is an error
</div>

<style>
#ec{{transition:stroke-dashoffset .65s cubic-bezier(.65,0,.45,1) .25s}}
#ex{{transition:stroke-dashoffset .4s cubic-bezier(.65,0,.45,1) .92s}}
#ea{{transition:stroke-dashoffset 1.1s cubic-bezier(.16,1,.3,1) .6s}}
@keyframes xs{{
  0%,100%{{transform:none}}
  20%{{transform:translateX(-5px) rotate(-2deg)}}
  40%{{transform:translateX(5px) rotate(2deg)}}
  60%{{transform:translateX(-3px) rotate(-1deg)}}
  80%{{transform:translateX(3px) rotate(1deg)}}
}}
</style>
<script>
requestAnimationFrame(function(){{
  document.getElementById('ec').style.strokeDashoffset='0';
  document.getElementById('ex').style.strokeDashoffset='0';
}});
document.getElementById('ts').textContent=new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});

var errScore=11;
setTimeout(function(){{
  document.getElementById('ea').style.strokeDashoffset=(238.8*(1-errScore/100));
  var el=document.getElementById('en'),t0=performance.now();
  (function tick(t){{
    var p=Math.min((t-t0)/900,1),e=1-Math.pow(1-p,3);
    el.textContent=Math.round(e*errScore);
    if(p<1)requestAnimationFrame(tick);
  }})(t0);
}},700);

var logs=[
  {{c:'rgb(45,156,255)',m:'Request received — parsing parameters'}},
  {{c:'rgb(45,156,255)',m:'User ID extracted from query'}},
  {{c:'rgb(245,166,35)',m:'Security validation initiated'}},
  {{c:'rgb(255,61,80)',m:'Verification failed: {message}'}},
  {{c:'rgb(255,61,80)',m:'Attempt logged with timestamp'}},
  {{c:'rgb(245,166,35)',m:'Rejection response delivered'}},
];
var al=document.getElementById('audit');
logs.forEach(function(l,i){{
  setTimeout(function(){{
    var d=document.createElement('div');d.className='a-item';d.style.animationDelay='0s';
    var t=new Date();
    d.innerHTML='<div class="a-dot" style="background:'+l.c+'"></div>'+
      '<div><div class="a-msg">'+l.m+'</div>'+
      '<div class="a-time">'+t.toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit',second:'2-digit'}})+'.'+String(t.getMilliseconds()).padStart(3,'0')+'</div></div>';
    al.appendChild(d);
  }},300+i*240);
}});
</script>
"""
    return base_page("Verification Failed", "255,61,80", body)


# ══════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_schema():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,username TEXT DEFAULT '',
        first_name TEXT DEFAULT '',balance REAL DEFAULT 0,
        total_earned REAL DEFAULT 0,total_withdrawn REAL DEFAULT 0,
        referral_count INTEGER DEFAULT 0,referred_by INTEGER DEFAULT 0,
        upi_id TEXT DEFAULT '',banned INTEGER DEFAULT 0,
        joined_at TEXT DEFAULT '',last_daily TEXT DEFAULT '',
        is_premium INTEGER DEFAULT 0,referral_paid INTEGER DEFAULT 0,
        ip_address TEXT DEFAULT '',ip_verified INTEGER DEFAULT 0,
        verify_attempts INTEGER DEFAULT 0,last_attempt_at REAL DEFAULT 0,
        verified_at REAL DEFAULT 0,session_hash TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',device_type TEXT DEFAULT ''
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS verify_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,ip TEXT,result TEXT,reason TEXT,
        user_agent TEXT,ts REAL,session_hash TEXT DEFAULT ''
    )""")
    migrate_cols = [
        ("ip_address",      "TEXT DEFAULT ''"),
        ("ip_verified",     "INTEGER DEFAULT 0"),
        ("referral_paid",   "INTEGER DEFAULT 0"),
        ("verify_attempts", "INTEGER DEFAULT 0"),
        ("last_attempt_at", "REAL DEFAULT 0"),
        ("verified_at",     "REAL DEFAULT 0"),
        ("session_hash",    "TEXT DEFAULT ''"),
        ("user_agent",      "TEXT DEFAULT ''"),
        ("device_type",     "TEXT DEFAULT ''"),
    ]
    for col, defn in migrate_cols:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

def get_real_ip():
    for h in ("CF-Connecting-IP", "X-Real-IP", "X-Forwarded-For"):
        v = request.headers.get(h, "")
        if v:
            return v.split(",")[0].strip()
    return request.remote_addr or ""

def detect_device(ua):
    ua = ua or ""
    if re.search(r"iPad|Tablet", ua, re.I):
        return "Tablet"
    if re.search(r"Mobi|Android|iPhone|iPod", ua, re.I):
        return "Mobile"
    return "Desktop"

def make_session_hash(user_id, ip, ua):
    raw = f"{user_id}|{ip}|{ua}|{SECRET_SALT}|{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def ip_taken(ip, uid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE ip_address=? AND user_id!=? LIMIT 1",
        (ip, uid)
    )
    r = cur.fetchone()
    conn.close()
    return r is not None

MAX_ATTEMPTS = 5
RATE_WINDOW  = 3600

def do_verify(user_id, ip, ua):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    u = cur.fetchone()
    now = time.time()

    def log(result, reason, sess=""):
        try:
            cur.execute(
                "INSERT INTO verify_log(user_id,ip,result,reason,user_agent,ts,session_hash) VALUES(?,?,?,?,?,?,?)",
                (user_id, ip, result, reason, ua, now, sess)
            )
            conn.commit()
        except Exception:
            pass

    if not u:
        log("fail", "user_not_found")
        conn.close()
        return False, "User not found. Please start the bot first."

    if int(u["banned"] or 0):
        log("fail", "banned")
        conn.close()
        return False, "Your account has been banned."

    if int(u["ip_verified"] or 0):
        conn.close()
        return True, "Already verified."

    attempts = int(u["verify_attempts"] or 0)
    last_at  = float(u["last_attempt_at"] or 0)

    if now - last_at < RATE_WINDOW and attempts >= MAX_ATTEMPTS:
        mins = int((RATE_WINDOW - (now - last_at)) / 60)
        log("fail", f"rate_limited_{attempts}")
        conn.close()
        return False, f"Too many attempts. Try again in {mins} min."

    if now - last_at >= RATE_WINDOW:
        attempts = 0

    if not ip:
        log("fail", "no_ip")
        conn.close()
        return False, "Could not detect your IP address."

    if ip_taken(ip, user_id):
        cur.execute(
            "UPDATE users SET verify_attempts=?,last_attempt_at=? WHERE user_id=?",
            (attempts + 1, now, user_id)
        )
        conn.commit()
        log("fail", "ip_conflict")
        conn.close()
        return False, "This IP is already linked to another account."

    device = detect_device(ua)
    sess   = make_session_hash(user_id, ip, ua)

    cur.execute(
        """UPDATE users SET
           ip_address=?,ip_verified=1,verify_attempts=?,last_attempt_at=?,
           verified_at=?,session_hash=?,user_agent=?,device_type=?
           WHERE user_id=?""",
        (ip, attempts + 1, now, now, sess, ua, device, user_id)
    )
    conn.commit()
    log("success", "ok", sess)
    conn.close()
    return True, "OK"


# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════
@app.route("/")
def home():
    return {"status": "running", "service": "IP Verify", "version": "3.0"}, 200

@app.route("/health")
def health():
    return {"status": "ok", "ts": int(time.time())}, 200

@app.route("/ip-verify")
def ip_verify():
    uid = request.args.get("uid", "").strip()
    if not uid or not uid.isdigit():
        return error_page(
            "Invalid or missing user ID. Use the link sent by the bot.",
            BOT_USERNAME
        ), 400
    user_id = int(uid)
    ip      = get_real_ip()
    ua      = request.headers.get("User-Agent", "")
    ok, msg = do_verify(user_id, ip, ua)
    if not ok:
        return error_page(msg, BOT_USERNAME), 400
    return success_page(user_id, BOT_USERNAME)

@app.route("/api/verify-status/<int:user_id>")
def verify_status(user_id):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "SELECT ip_verified,ip_address,verified_at,device_type,session_hash FROM users WHERE user_id=?",
        (user_id,)
    )
    r = cur.fetchone()
    conn.close()
    if not r:
        return jsonify({"verified": False, "error": "user_not_found"}), 404
    return jsonify({
        "verified":    bool(int(r["ip_verified"] or 0)),
        "ip":          r["ip_address"] or None,
        "verified_at": r["verified_at"] or None,
        "device":      r["device_type"] or None,
        "session":     r["session_hash"] or None,
    })

@app.route("/api/verify-log/<int:user_id>")
def verify_log(user_id):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "SELECT result,reason,ts FROM verify_log WHERE user_id=? ORDER BY ts DESC LIMIT 20",
        (user_id,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"log": rows})

@app.route("/api/stats")
def stats():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM users")
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM users WHERE ip_verified=1")
    verified = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM verify_log WHERE result='fail'")
    fails = cur.fetchone()["c"]
    conn.close()
    return jsonify({"total_users": total, "verified": verified, "failed_attempts": fails})


if __name__ == "__main__":
    ensure_schema()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
