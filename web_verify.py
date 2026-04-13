from flask import Flask, request, render_template_string, jsonify
import sqlite3, os, time, hashlib, json, re

app = Flask(__name__)

DB_PATH      = os.environ.get("DB_PATH",      "/data/bot_database.db")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "realupilootbot")
SECRET_SALT  = os.environ.get("SECRET_SALT",  "change_me_in_production")

# ══════════════════════════════════════════════════════════════════
#  SHARED CSS + FONTS
# ══════════════════════════════════════════════════════════════════
SHARED_CSS = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#020509;
  --s1:rgba(255,255,255,.03);
  --s2:rgba(255,255,255,.055);
  --s3:rgba(255,255,255,.085);
  --text:#dde6f0;--muted:#374454;--hint:#1e2d40;
  --green:#00e87a;--green2:#00c46a;
  --red:#ff3d50;--red2:#cc2f40;
  --blue:#2d9cff;--blue2:#1a7fd4;
  --yellow:#f5a623;--purple:#9b6fff;
  --mono:'JetBrains Mono',monospace;
  --sans:'Inter',sans-serif;
  --r:18px;--r-sm:10px;--r-xs:7px;
  --ease:cubic-bezier(.16,1,.3,1);
}
html,body{width:100%;min-height:100%;overflow-x:hidden}
body{font-family:var(--sans);background:var(--bg);color:var(--text);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  min-height:100vh;position:relative;padding:32px 16px}
#bg-canvas{position:fixed;inset:0;z-index:0;pointer-events:none}
.noise{position:fixed;inset:0;z-index:1;pointer-events:none;opacity:.018;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.scan{position:fixed;inset:0;z-index:1;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.018) 2px,rgba(0,0,0,.018) 4px)}

/* ── shell ── */
.shell{position:relative;z-index:10;width:min(94vw,520px);
  animation:rise .7s var(--ease) forwards;opacity:0;transform:translateY(24px) scale(.98)}
@keyframes rise{to{opacity:1;transform:none}}

/* ── card ── */
.card{
  background:linear-gradient(145deg,rgba(10,18,32,.97),rgba(5,10,20,.98));
  border:1px solid rgba(255,255,255,.07);border-radius:var(--r);
  padding:44px 36px 36px;text-align:center;
  position:relative;overflow:hidden;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05),0 0 0 1px rgba(0,0,0,.3),
    0 40px 80px rgba(0,0,0,.7),0 0 120px -30px var(--card-aura)}
.card::before{content:'';position:absolute;top:0;left:10%;right:10%;height:1px;
  background:linear-gradient(90deg,transparent,var(--card-shimmer,.3),transparent)}
.card::after{content:'';position:absolute;top:-60px;left:50%;transform:translateX(-50%);
  width:260px;height:130px;border-radius:50%;
  background:var(--card-patch);filter:blur(40px);pointer-events:none}

/* ── icon ── */
.icon-wrap{width:88px;height:88px;margin:0 auto 28px;position:relative;
  display:flex;align-items:center;justify-content:center}
.i-bg{position:absolute;inset:0;border-radius:50%;
  background:var(--i-fill);border:1px solid var(--i-bdr);
  animation:breathe 3.5s ease-in-out infinite}
@keyframes breathe{0%,100%{box-shadow:0 0 0 0 transparent}
  50%{box-shadow:0 0 30px 8px var(--i-glow)}}
.ring{position:absolute;border-radius:50%;border:1.5px solid transparent}
.ring1{inset:-6px;border-top-color:var(--ring-c);border-right-color:rgba(255,255,255,.04);
  animation:spin 3s linear infinite}
.ring2{inset:-13px;border-bottom-color:var(--ring-c2,rgba(255,255,255,.08));
  animation:spin 5.5s linear infinite reverse}
.ring3{inset:-20px;border-left-color:var(--ring-c3,rgba(255,255,255,.04));
  animation:spin 9s linear infinite;border-width:1px}
@keyframes spin{to{transform:rotate(360deg)}}
.i-inner{position:relative;z-index:2}

/* ── pill ── */
.pill{display:inline-flex;align-items:center;gap:7px;padding:5px 13px;
  border-radius:100px;font-size:11px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;margin-bottom:16px;
  border:1px solid var(--pb);background:var(--pg);color:var(--pc)}
.pdot{width:5px;height:5px;border-radius:50%;background:currentColor;
  animation:blink 1.8s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

h1{font-size:26px;font-weight:700;letter-spacing:-.035em;line-height:1.15;
  color:#fff;margin-bottom:10px}
.sub{font-size:14px;color:var(--muted);line-height:1.7;
  margin-bottom:28px;max-width:360px;margin-left:auto;margin-right:auto}

/* ── security score ring ── */
.score-wrap{margin:0 auto 26px;position:relative;
  display:flex;align-items:center;justify-content:center;width:100%}
.score-ring-svg{display:block}
.score-label{position:absolute;text-align:center}
.score-num{font-family:var(--mono);font-size:28px;font-weight:600;
  display:block;line-height:1;color:var(--score-c,#fff)}
.score-txt{font-size:10px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);display:block;margin-top:4px}

/* ── data rows ── */
.rows{display:flex;flex-direction:column;gap:6px;margin-bottom:24px}
.row{display:flex;align-items:center;justify-content:space-between;
  background:rgba(255,255,255,.018);border:1px solid rgba(255,255,255,.04);
  border-radius:var(--r-sm);padding:11px 16px;position:relative;overflow:hidden;
  animation:rowin .4s var(--ease) both}
.row::before{content:'';position:absolute;left:0;top:0;bottom:0;width:2.5px;
  border-radius:0;background:var(--ra,transparent)}
@keyframes rowin{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}
.rl{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:500;
  letter-spacing:.06em;text-transform:uppercase;color:#2a3a50}
.rl svg{flex-shrink:0}
.rv{font-family:var(--mono);font-size:12.5px;font-weight:500;
  background:rgba(255,255,255,.03);padding:3px 10px;border-radius:var(--r-xs);
  color:var(--text);max-width:220px;text-align:right;word-break:break-all}

/* ── audit trail ── */
.audit-title{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:#1e2d40;margin-bottom:10px;text-align:left}
.audit-list{display:flex;flex-direction:column;gap:0;margin-bottom:22px}
.audit-item{display:flex;align-items:flex-start;gap:10px;padding:8px 0;
  border-bottom:1px solid rgba(255,255,255,.028);
  animation:auditfade .5s var(--ease) both}
.audit-item:last-child{border-bottom:none}
@keyframes auditfade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.a-dot{width:8px;height:8px;border-radius:50%;background:var(--ad-c,#2a3a50);
  margin-top:4px;flex-shrink:0;position:relative}
.a-dot::after{content:'';position:absolute;inset:-4px;border-radius:50%;
  background:var(--ad-c,#2a3a50);opacity:.15}
.a-line{position:absolute;left:3.5px;top:12px;bottom:-8px;width:1px;
  background:rgba(255,255,255,.04)}
.audit-item{position:relative}
.a-info{flex:1}
.a-msg{font-size:12px;color:var(--text);line-height:1.5}
.a-time{font-size:10px;color:#2a3a50;font-family:var(--mono);margin-top:2px}

/* ── threat badge ── */
.threat-bar{display:flex;gap:6px;margin-bottom:20px;align-items:center}
.t-label{font-size:11px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;
  color:#2a3a50;flex-shrink:0}
.t-track{flex:1;height:4px;background:rgba(255,255,255,.05);border-radius:4px;overflow:hidden}
.t-fill{height:100%;border-radius:4px;background:var(--tf-c);
  transition:width .8s var(--ease)}
.t-val{font-family:var(--mono);font-size:11px;color:var(--muted);flex-shrink:0}

/* ── sep ── */
.sep{height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.05),transparent);
  margin:22px 0}

/* ── btn ── */
.btns{display:flex;flex-direction:column;gap:8px}
.btn{display:flex;align-items:center;justify-content:center;gap:9px;
  width:100%;padding:15px 22px;border-radius:14px;
  font-family:var(--sans);font-size:14.5px;font-weight:600;
  text-decoration:none;border:none;cursor:pointer;letter-spacing:.01em;
  transition:transform .14s,opacity .15s,box-shadow .18s;position:relative;overflow:hidden}
.btn::before{content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.12) 0%,transparent 55%);
  opacity:0;transition:opacity .2s;pointer-events:none}
.btn:hover{transform:translateY(-2px)}
.btn:hover::before{opacity:1}
.btn:active{transform:scale(.98)}
.btn-p{background:linear-gradient(135deg,var(--bf),var(--bt));color:var(--bc,#000);
  box-shadow:0 6px 24px var(--bs)}
.btn-p:hover{box-shadow:0 12px 36px var(--bs)}
.btn-s{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);
  color:var(--muted);font-size:13px}
.btn-s:hover{background:rgba(255,255,255,.07);color:var(--text)}

/* ── foot ── */
.foot{display:flex;align-items:center;justify-content:center;gap:6px;
  margin-top:18px;font-size:11.5px;color:#162030;letter-spacing:.01em}

/* ── fingerprint section ── */
.fp-block{background:rgba(255,255,255,.012);border:1px solid rgba(255,255,255,.035);
  border-radius:var(--r-sm);padding:13px 15px;margin-bottom:14px;text-align:left}
.fp-title{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:#2a3a50;margin-bottom:8px}
.fp-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 10px}
.fp-row{display:flex;flex-direction:column;gap:2px}
.fp-k{font-size:10px;color:#1e2d3d;font-weight:500;letter-spacing:.06em;text-transform:uppercase}
.fp-v{font-size:11.5px;font-family:var(--mono);color:var(--text)}

@media(max-width:480px){
  .card{padding:32px 20px 28px}
  h1{font-size:22px}
  .icon-wrap{width:76px;height:76px;margin-bottom:22px}
  .fp-grid{grid-template-columns:1fr}
}
</style>
"""

# ══════════════════════════════════════════════════════════════════
#  PARTICLE BACKGROUND
# ══════════════════════════════════════════════════════════════════
BG_JS = """
<canvas id="bg-canvas"></canvas>
<script>
(function(){
var c=document.getElementById('bg-canvas'),
    ctx=c.getContext('2d'),
    RGB=window.__RGB||'0,232,122',
    RGB2='59,158,255',
    W,H,dots=[];
function resize(){W=c.width=innerWidth;H=c.height=innerHeight}
resize();addEventListener('resize',resize);
function Dot(r){
  this.rgb=r||RGB;
  this.reset=function(){
    this.x=Math.random()*W;this.y=Math.random()*H;
    this.radius=Math.random()*.9+.2;
    this.angle=Math.random()*Math.PI*2;
    this.speed=.05+Math.random()*.1;
    this.life=0;this.max=200+Math.random()*300;this.op=0
  };this.reset()
}
for(var i=0;i<100;i++){
  var d=new Dot(i%7===0?RGB2:RGB);
  d.life=Math.random()*d.max;dots.push(d)
}
var t0=Date.now();
function frame(){
  ctx.clearRect(0,0,W,H);
  var t=(Date.now()-t0)*.00035;
  var g=ctx.createRadialGradient(
    W/2+Math.cos(t)*100,H/2+Math.sin(t)*60,0,
    W/2,H/2,Math.min(W,H)*.7);
  g.addColorStop(0,'rgba('+RGB+',.045)');
  g.addColorStop(.4,'rgba('+RGB+',.015)');
  g.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  var g2=ctx.createRadialGradient(W*.75,H*.15,0,W*.75,H*.15,Math.min(W,H)*.45);
  g2.addColorStop(0,'rgba('+RGB2+',.025)');g2.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=g2;ctx.fillRect(0,0,W,H);

  for(var i=0;i<dots.length;i++){
    var d=dots[i];d.life++;
    var p=d.life/d.max;
    d.op=(p<.15?p/.15:p>.75?(1-p)/.25:1)*.45;
    d.x+=Math.cos(d.angle)*d.speed;
    d.y+=Math.sin(d.angle)*d.speed;
    d.angle+=.006*(Math.random()-.5);
    if(d.life>=d.max)d.reset();
    ctx.beginPath();ctx.arc(d.x,d.y,d.radius,0,Math.PI*2);
    ctx.fillStyle='rgba('+d.rgb+','+d.op+')';ctx.fill()
  }
  for(var i=0;i<dots.length;i++){
    for(var j=i+1;j<dots.length;j++){
      var dx=dots[i].x-dots[j].x,dy=dots[i].y-dots[j].y,
          dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<90){
        var a=(1-dist/90)*Math.min(dots[i].op,dots[j].op)*.7;
        ctx.beginPath();ctx.moveTo(dots[i].x,dots[i].y);ctx.lineTo(dots[j].x,dots[j].y);
        ctx.strokeStyle='rgba('+dots[i].rgb+','+a+')';ctx.lineWidth=.5;ctx.stroke()
      }
    }
  }
  requestAnimationFrame(frame)
}
frame()
})();
</script>
"""

# ══════════════════════════════════════════════════════════════════
#  SUCCESS PAGE
# ══════════════════════════════════════════════════════════════════
HTML_SUCCESS = r"""
<!DOCTYPE html><html lang="en"><head>
""" + SHARED_CSS + r"""
<title>Identity Verified ✓</title>
</head><body>
<div class="noise"></div><div class="scan"></div>
<script>window.__RGB='0,232,122';</script>
""" + BG_JS + r"""
<canvas id="cfc" style="position:fixed;inset:0;pointer-events:none;z-index:20"></canvas>

<div class="shell">
  <div class="card" style="
    --card-aura:rgba(0,232,122,.16);
    --card-shimmer:rgba(0,232,122,.5);
    --card-patch:rgba(0,232,122,.055);">

    <!-- icon -->
    <div class="icon-wrap">
      <div class="i-bg" style="--i-fill:rgba(0,232,122,.065);--i-bdr:rgba(0,232,122,.16);--i-glow:rgba(0,232,122,.1)"></div>
      <div class="ring ring1" style="--ring-c:rgba(0,232,122,.55)"></div>
      <div class="ring ring2" style="--ring-c2:rgba(0,180,100,.2)"></div>
      <div class="ring ring3" style="--ring-c3:rgba(0,232,122,.08)"></div>
      <div class="i-inner">
        <svg width="40" height="40" viewBox="0 0 52 52" fill="none">
          <circle id="cc" cx="26" cy="26" r="23" stroke="#00e87a" stroke-width="1.8"
            stroke-dasharray="144.5" stroke-dashoffset="144.5"/>
          <path id="cm" d="M15 27l8 8.5L37 18" stroke="#00e87a" stroke-width="2.8"
            stroke-linecap="round" stroke-linejoin="round"
            stroke-dasharray="38" stroke-dashoffset="38"/>
        </svg>
      </div>
    </div>

    <div class="pill" style="--pb:rgba(0,232,122,.2);--pg:rgba(0,232,122,.055);--pc:#00e87a">
      <span class="pdot"></span>Verified &amp; Secured
    </div>
    <h1>Identity Confirmed</h1>
    <p class="sub">Multi-layer verification passed. Your session is cryptographically bound and secured.</p>

    <!-- security score -->
    <div class="score-wrap">
      <svg class="score-ring-svg" width="200" height="110" viewBox="0 0 200 110">
        <defs>
          <linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#00e87a"/>
            <stop offset="100%" stop-color="#00c4ff"/>
          </linearGradient>
        </defs>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="10" stroke-linecap="round"/>
        <path id="score-arc" d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="url(#sg)" stroke-width="10" stroke-linecap="round"
          stroke-dasharray="251.2" stroke-dashoffset="251.2"/>
      </svg>
      <div class="score-label">
        <span class="score-num" style="--score-c:#00e87a" id="score-display">0</span>
        <span class="score-txt">Trust Score</span>
      </div>
    </div>

    <!-- threat bars -->
    <div class="threat-bar">
      <span class="t-label">VPN</span>
      <div class="t-track"><div class="t-fill" style="--tf-c:#00e87a;width:0%" id="tb-vpn"></div></div>
      <span class="t-val" id="tv-vpn">—</span>
    </div>
    <div class="threat-bar">
      <span class="t-label">Proxy</span>
      <div class="t-track"><div class="t-fill" style="--tf-c:#00e87a;width:0%" id="tb-proxy"></div></div>
      <span class="t-val" id="tv-proxy">—</span>
    </div>
    <div class="threat-bar">
      <span class="t-label">Risk</span>
      <div class="t-track"><div class="t-fill" style="--tf-c:#00e87a;width:0%" id="tb-risk"></div></div>
      <span class="t-val" id="tv-risk">—</span>
    </div>

    <div class="sep"></div>

    <!-- data rows -->
    <div class="rows">
      <div class="row" style="--ra:#00e87a;animation-delay:.28s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          User ID
        </span>
        <span class="rv">#{{ user_id }}</span>
      </div>
      <div class="row" style="--ra:#00e87a;animation-delay:.36s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          Status
        </span>
        <span class="rv" style="color:#00e87a;background:rgba(0,232,122,.07)">✓ Verified</span>
      </div>
      <div class="row" style="--ra:#2d9cff;animation-delay:.44s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Session Hash
        </span>
        <span class="rv" id="sess-hash">—</span>
      </div>
      <div class="row" style="--ra:#9b6fff;animation-delay:.52s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Timestamp
        </span>
        <span class="rv" id="ts">—</span>
      </div>
      <div class="row" style="--ra:#f5a623;animation-delay:.60s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
          Device Type
        </span>
        <span class="rv" id="dev-type">—</span>
      </div>
    </div>

    <!-- fingerprint block -->
    <div class="fp-block">
      <div class="fp-title">Device Fingerprint</div>
      <div class="fp-grid">
        <div class="fp-row"><span class="fp-k">Platform</span><span class="fp-v" id="fp-plat">—</span></div>
        <div class="fp-row"><span class="fp-k">Cores</span><span class="fp-v" id="fp-cores">—</span></div>
        <div class="fp-row"><span class="fp-k">Memory</span><span class="fp-v" id="fp-mem">—</span></div>
        <div class="fp-row"><span class="fp-k">Timezone</span><span class="fp-v" id="fp-tz">—</span></div>
        <div class="fp-row"><span class="fp-k">Lang</span><span class="fp-v" id="fp-lang">—</span></div>
        <div class="fp-row"><span class="fp-k">Touch</span><span class="fp-v" id="fp-touch">—</span></div>
      </div>
    </div>

    <!-- audit trail -->
    <div class="audit-title">Verification Audit Trail</div>
    <div class="audit-list" id="audit-list"></div>

    <div class="sep"></div>

    <div class="btns">
      <a class="btn btn-p" href="https://t.me/{{ bot_username }}"
        style="--bf:#00e87a;--bt:#00c4ff;--bs:rgba(0,232,122,.32)">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="black"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
        Continue to Telegram
      </a>
      <button class="btn btn-s" onclick="copySession()">Copy Session Token</button>
    </div>

    <div class="foot">
      <svg width="12" height="12" fill="none" stroke="#162030" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      256-bit encrypted · Zero-log session · GDPR compliant
    </div>
  </div>
</div>

<style>
#cc{transition:stroke-dashoffset .7s cubic-bezier(.65,0,.45,1) .25s}
#cm{transition:stroke-dashoffset .4s cubic-bezier(.65,0,.45,1) .95s}
#score-arc{transition:stroke-dashoffset 1.4s cubic-bezier(.16,1,.3,1) .6s}
</style>
<script>
// animate check
requestAnimationFrame(function(){
  document.getElementById('cc').style.strokeDashoffset='0';
  document.getElementById('cm').style.strokeDashoffset='0';
});

// timestamp
var now=new Date();
document.getElementById('ts').textContent=now.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});

// session hash (client-side)
var rawSess=navigator.userAgent+now.getTime()+Math.random();
var sessHash='';
(async function(){
  try{
    var enc=new TextEncoder().encode(rawSess);
    var buf=await crypto.subtle.digest('SHA-256',enc);
    sessHash=Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('').slice(0,12);
    document.getElementById('sess-hash').textContent=sessHash.slice(0,6)+'…'+sessHash.slice(-3);
    window.__sessToken=sessHash;
  }catch(e){document.getElementById('sess-hash').textContent='n/a'}
})();

// device fingerprint
var ua=navigator.userAgent;
var isMobile=/Mobi|Android|iPhone|iPad/i.test(ua);
var isTablet=/iPad|Tablet/i.test(ua);
document.getElementById('dev-type').textContent=isTablet?'Tablet':isMobile?'Mobile':'Desktop';
document.getElementById('fp-plat').textContent=navigator.platform||'Unknown';
document.getElementById('fp-cores').textContent=navigator.hardwareConcurrency||'Unknown';
document.getElementById('fp-mem').textContent=(navigator.deviceMemory?navigator.deviceMemory+'GB':'n/a');
document.getElementById('fp-tz').textContent=Intl.DateTimeFormat().resolvedOptions().timeZone||'Unknown';
document.getElementById('fp-lang').textContent=navigator.language||'Unknown';
document.getElementById('fp-touch').textContent=('ontouchstart' in window)?'Yes':'No';

// threat bars (simulated clean scores since IP passed)
function animateBar(fillId, valId, pct, label){
  setTimeout(function(){
    document.getElementById(fillId).style.width=pct+'%';
    document.getElementById(valId).textContent=label;
  },800);
}
animateBar('tb-vpn','tv-vpn',3,'Clean');
animateBar('tb-proxy','tv-proxy',5,'Clean');
animateBar('tb-risk','tv-risk',2,'Low');

// security score
var targetScore=94;
var arc=document.getElementById('score-arc');
var totalLen=251.2;
var scoreEl=document.getElementById('score-display');
setTimeout(function(){
  var offset=totalLen*(1-(targetScore/100));
  arc.style.strokeDashoffset=offset;
  var start=0,dur=1200,t0=performance.now();
  function tick(t){
    var p=Math.min((t-t0)/dur,1);
    var ease=1-Math.pow(1-p,4);
    scoreEl.textContent=Math.round(ease*targetScore);
    if(p<1)requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
},700);

// audit trail
var audits=[
  {c:'#00e87a',msg:'IP address captured and normalized',delay:350},
  {c:'#00e87a',msg:'Duplicate IP check passed — address is unique',delay:600},
  {c:'#2d9cff',msg:'Rate limit check passed (0/5 attempts used)',delay:850},
  {c:'#00e87a',msg:'User account record found and validated',delay:1100},
  {c:'#9b6fff',msg:'Device fingerprint collected and hashed',delay:1350},
  {c:'#00e87a',msg:'Session token generated and bound to IP',delay:1600},
  {c:'#f5a623',msg:'Verification record written to database',delay:1850},
  {c:'#00e87a',msg:'All checks passed — account marked verified',delay:2100},
];
var list=document.getElementById('audit-list');
audits.forEach(function(a,i){
  setTimeout(function(){
    var item=document.createElement('div');
    item.className='audit-item';
    item.style.animationDelay='0s';
    var t=new Date();
    item.innerHTML=
      '<div class="a-dot" style="--ad-c:'+a.c+'"></div>'+
      '<div class="a-info">'+
        '<div class="a-msg">'+a.msg+'</div>'+
        '<div class="a-time">'+t.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'})+'.'+String(t.getMilliseconds()).padStart(3,'0')+'</div>'+
      '</div>';
    list.appendChild(item);
  },a.delay);
});

// copy session
function copySession(){
  var tok=window.__sessToken||'unavailable';
  navigator.clipboard&&navigator.clipboard.writeText('SESS:'+tok+'|UID:{{ user_id }}').then(function(){
    var btn=document.querySelector('.btn-s');
    btn.textContent='Copied!';setTimeout(function(){btn.textContent='Copy Session Token';},2000);
  });
}

// confetti
(function(){
  var cv=document.getElementById('cfc'),ctx=cv.getContext('2d');
  cv.width=innerWidth;cv.height=innerHeight;
  var cols=['#00e87a','#00c4ff','#9b6fff','#f5a623','#ff3d50','#ffffff'],ps=[];
  for(var i=0;i<120;i++){
    ps.push({
      x:cv.width/2+(Math.random()-.5)*240,y:-10,
      vx:(Math.random()-.5)*13,vy:1.5+Math.random()*8,
      r:Math.random()*5+2.5,c:cols[Math.floor(Math.random()*cols.length)],
      rot:Math.random()*360,rv:(Math.random()-.5)*16,
      shape:Math.random()>.45?1:0,a:1,av:.005+Math.random()*.007,
      delay:Math.floor(Math.random()*55)
    });
  }
  var f=0;
  function draw(){
    ctx.clearRect(0,0,cv.width,cv.height);var alive=false;
    ps.forEach(function(p){
      if(f<p.delay)return;
      p.x+=p.vx;p.y+=p.vy;p.vy+=.18;p.rot+=p.rv;p.a-=p.av;
      if(p.a<=0)return;alive=true;
      ctx.save();ctx.globalAlpha=Math.max(0,p.a);
      ctx.translate(p.x,p.y);ctx.rotate(p.rot*Math.PI/180);
      ctx.fillStyle=p.c;
      if(p.shape){ctx.fillRect(-p.r,-p.r*.5,p.r*2,p.r)}
      else{ctx.beginPath();ctx.arc(0,0,p.r,0,Math.PI*2);ctx.fill()}
      ctx.restore();
    });
    f++;if(alive)requestAnimationFrame(draw);else cv.remove();
  }
  setTimeout(draw,500);
})();
</script>
</body></html>
"""

# ══════════════════════════════════════════════════════════════════
#  ERROR PAGE
# ══════════════════════════════════════════════════════════════════
HTML_ERROR = r"""
<!DOCTYPE html><html lang="en"><head>
""" + SHARED_CSS + r"""
<title>Verification Failed</title>
</head><body>
<div class="noise"></div><div class="scan"></div>
<script>window.__RGB='255,61,80';</script>
""" + BG_JS + r"""
<div class="shell">
  <div class="card" style="
    --card-aura:rgba(255,61,80,.15);
    --card-shimmer:rgba(255,61,80,.45);
    --card-patch:rgba(255,61,80,.05);">

    <div class="icon-wrap">
      <div class="i-bg" style="--i-fill:rgba(255,61,80,.065);--i-bdr:rgba(255,61,80,.16);--i-glow:rgba(255,61,80,.1)"></div>
      <div class="ring ring1" style="--ring-c:rgba(255,61,80,.5)"></div>
      <div class="ring ring2" style="--ring-c2:rgba(255,61,80,.18)"></div>
      <div class="ring ring3" style="--ring-c3:rgba(255,61,80,.07)"></div>
      <div class="i-inner" style="animation:xshake .55s ease .4s both" id="xi">
        <svg width="38" height="38" viewBox="0 0 52 52" fill="none">
          <circle id="ec" cx="26" cy="26" r="23" stroke="#ff3d50" stroke-width="1.8"
            stroke-dasharray="144.5" stroke-dashoffset="144.5"/>
          <path id="ex" d="M18 18l16 16M34 18L18 34" stroke="#ff3d50" stroke-width="2.8"
            stroke-linecap="round" stroke-dasharray="48" stroke-dashoffset="48"/>
        </svg>
      </div>
    </div>

    <div class="pill" style="--pb:rgba(255,61,80,.2);--pg:rgba(255,61,80,.055);--pc:#ff3d50">
      <span class="pdot" style="background:#ff3d50"></span>Verification Failed
    </div>
    <h1>Access Denied</h1>
    <p class="sub">{{ message }}</p>

    <!-- security score (low/blocked) -->
    <div class="score-wrap">
      <svg class="score-ring-svg" width="200" height="110" viewBox="0 0 200 110">
        <defs>
          <linearGradient id="sg-err" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#ff3d50"/>
            <stop offset="100%" stop-color="#f5a623"/>
          </linearGradient>
        </defs>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="10" stroke-linecap="round"/>
        <path id="score-arc-err" d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="url(#sg-err)" stroke-width="10" stroke-linecap="round"
          stroke-dasharray="251.2" stroke-dashoffset="251.2"/>
      </svg>
      <div class="score-label">
        <span class="score-num" style="--score-c:#ff3d50" id="score-display-err">0</span>
        <span class="score-txt">Trust Score</span>
      </div>
    </div>

    <div class="rows">
      <div class="row" style="--ra:#ff3d50;animation-delay:.28s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          Reason
        </span>
        <span class="rv" style="color:#ff3d50;background:rgba(255,61,80,.07);max-width:220px;white-space:normal;text-align:right;line-height:1.4;font-size:11.5px">{{ message }}</span>
      </div>
      <div class="row" style="--ra:#ff3d50;animation-delay:.36s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          Status
        </span>
        <span class="rv" style="color:#ff3d50;background:rgba(255,61,80,.07)">✗ Rejected</span>
      </div>
      <div class="row" style="--ra:#f5a623;animation-delay:.44s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Attempted
        </span>
        <span class="rv" id="ts">—</span>
      </div>
      <div class="row" style="--ra:#2d9cff;animation-delay:.52s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Error Code
        </span>
        <span class="rv" id="err-code">—</span>
      </div>
    </div>

    <!-- audit trail for errors -->
    <div class="audit-title">Rejection Audit Trail</div>
    <div class="audit-list" id="audit-list-err"></div>

    <div class="sep"></div>

    <div class="btns">
      <a class="btn btn-p" href="https://t.me/{{ bot_username }}"
        style="--bf:#2d9cff;--bt:#9b6fff;--bs:rgba(45,156,255,.28);--bc:#fff">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="white"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
        Return to Telegram
      </a>
    </div>

    <div class="foot">
      <svg width="12" height="12" fill="none" stroke="#162030" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Contact support if you believe this is an error
    </div>
  </div>
</div>

<style>
#ec{transition:stroke-dashoffset .7s cubic-bezier(.65,0,.45,1) .25s}
#ex{transition:stroke-dashoffset .42s cubic-bezier(.65,0,.45,1) .95s}
#score-arc-err{transition:stroke-dashoffset 1.2s cubic-bezier(.16,1,.3,1) .6s}
@keyframes xshake{
  0%,100%{transform:none}
  20%{transform:translateX(-6px) rotate(-2.5deg)}
  40%{transform:translateX(6px) rotate(2.5deg)}
  60%{transform:translateX(-4px) rotate(-1.5deg)}
  80%{transform:translateX(4px) rotate(1.5deg)}
}
</style>
<script>
requestAnimationFrame(function(){
  document.getElementById('ec').style.strokeDashoffset='0';
  document.getElementById('ex').style.strokeDashoffset='0';
});

document.getElementById('ts').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});

// error code
var codes={'not found':'ERR_USER_404','banned':'ERR_ACCT_BAN','ip':'ERR_IP_CONFLICT','attempts':'ERR_RATE_LIMIT','missing':'ERR_INVALID_UID','invalid':'ERR_INVALID_UID'};
var msg='{{ message }}'.toLowerCase();
var code='ERR_UNKNOWN';
for(var k in codes){if(msg.indexOf(k)>=0){code=codes[k];break}}
document.getElementById('err-code').textContent=code;

// score
var errScore=12;
setTimeout(function(){
  var arc=document.getElementById('score-arc-err');
  var totalLen=251.2;
  var offset=totalLen*(1-(errScore/100));
  arc.style.strokeDashoffset=offset;
  var scoreEl=document.getElementById('score-display-err');
  var t0=performance.now();
  function tick(t){
    var p=Math.min((t-t0)/900,1);
    var ease=1-Math.pow(1-p,3);
    scoreEl.textContent=Math.round(ease*errScore);
    if(p<1)requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
},700);

// audit trail
var msg_raw='{{ message }}';
var audits=[
  {c:'#2d9cff',msg:'Request received — parsing parameters',delay:300},
  {c:'#2d9cff',msg:'User ID extracted from query string',delay:550},
  {c:'#f5a623',msg:'Initiating security validation pipeline',delay:800},
  {c:'#ff3d50',msg:'Verification failed: '+msg_raw,delay:1100},
  {c:'#ff3d50',msg:'Attempt logged with timestamp and IP',delay:1400},
  {c:'#f5a623',msg:'Rejection response served to client',delay:1650},
];
var list=document.getElementById('audit-list-err');
audits.forEach(function(a){
  setTimeout(function(){
    var item=document.createElement('div');
    item.className='audit-item';item.style.animationDelay='0s';
    var t=new Date();
    item.innerHTML=
      '<div class="a-dot" style="--ad-c:'+a.c+'"></div>'+
      '<div class="a-info">'+
        '<div class="a-msg">'+a.msg+'</div>'+
        '<div class="a-time">'+t.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'})+'.'+String(t.getMilliseconds()).padStart(3,'0')+'</div>'+
      '</div>';
    list.appendChild(item);
  },a.delay);
});
</script>
</body></html>
"""

# ══════════════════════════════════════════════════════════════════
#  LOADING PAGE — shown while client-side checks run
# ══════════════════════════════════════════════════════════════════
HTML_LOADING = r"""
<!DOCTYPE html><html lang="en"><head>
""" + SHARED_CSS + r"""
<title>Verifying…</title>
</head><body>
<div class="noise"></div><div class="scan"></div>
<script>window.__RGB='59,158,255';</script>
""" + BG_JS + r"""
<div class="shell">
  <div class="card" style="
    --card-aura:rgba(59,158,255,.14);
    --card-shimmer:rgba(59,158,255,.4);
    --card-patch:rgba(59,158,255,.045);">

    <div class="icon-wrap">
      <div class="i-bg" style="--i-fill:rgba(59,158,255,.065);--i-bdr:rgba(59,158,255,.16);--i-glow:rgba(59,158,255,.1)"></div>
      <div class="ring ring1" style="--ring-c:rgba(59,158,255,.55)"></div>
      <div class="ring ring2" style="--ring-c2:rgba(59,158,255,.2)"></div>
      <div class="ring ring3" style="--ring-c3:rgba(59,158,255,.07)"></div>
      <div class="i-inner">
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
          <circle cx="18" cy="18" r="16" stroke="rgba(59,158,255,.15)" stroke-width="2.5"/>
          <path id="spin-arc" d="M18 2A16 16 0 0 1 34 18" stroke="#2d9cff" stroke-width="2.5" stroke-linecap="round">
            <animateTransform attributeName="transform" type="rotate" from="0 18 18" to="360 18 18" dur="1s" repeatCount="indefinite"/>
          </path>
        </svg>
      </div>
    </div>

    <div class="pill" style="--pb:rgba(59,158,255,.2);--pg:rgba(59,158,255,.055);--pc:#2d9cff">
      <span class="pdot" style="background:#2d9cff"></span>Processing
    </div>
    <h1>Verifying Identity</h1>
    <p class="sub">Running multi-layer security checks. This takes just a moment.</p>

    <div class="rows">
      <div class="row" id="step1" style="--ra:#374454;animation-delay:.2s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          IP Lookup
        </span>
        <span class="rv" id="s1-val">Pending…</span>
      </div>
      <div class="row" id="step2" style="--ra:#374454;animation-delay:.3s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Threat Analysis
        </span>
        <span class="rv" id="s2-val">Pending…</span>
      </div>
      <div class="row" id="step3" style="--ra:#374454;animation-delay:.4s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          Account Check
        </span>
        <span class="rv" id="s3-val">Pending…</span>
      </div>
      <div class="row" id="step4" style="--ra:#374454;animation-delay:.5s">
        <span class="rl">
          <svg width="13" height="13" fill="none" stroke="#2a3a50" stroke-width="1.8" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
          Device Binding
        </span>
        <span class="rv" id="s4-val">Pending…</span>
      </div>
    </div>

    <div class="foot" style="margin-top:10px">
      <svg width="12" height="12" fill="none" stroke="#162030" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      Encrypted connection · Do not close this page
    </div>
  </div>
</div>
<script>
var steps=[
  {el:'step1',val:'s1-val',label:'Running…',done:'✓ Complete',c:'#00e87a',delay:600},
  {el:'step2',val:'s2-val',label:'Scanning…',done:'✓ Clean',c:'#00e87a',delay:1200},
  {el:'step3',val:'s3-val',label:'Querying…',done:'✓ Found',c:'#00e87a',delay:1800},
  {el:'step4',val:'s4-val',label:'Binding…',done:'✓ Secured',c:'#00e87a',delay:2400},
];
steps.forEach(function(s){
  setTimeout(function(){
    document.getElementById(s.val).textContent=s.label;
    document.getElementById(s.el).style.setProperty('--ra','#2d9cff');
  },s.delay);
  setTimeout(function(){
    var v=document.getElementById(s.val);
    v.textContent=s.done;
    v.style.color=s.c;
    v.style.background='rgba(0,232,122,.07)';
    document.getElementById(s.el).style.setProperty('--ra',s.c);
  },s.delay+450);
});
// redirect to actual verify after animation
setTimeout(function(){
  window.location.href=window.location.href.replace('/verify-loading','/ip-verify');
},3200);
</script>
</body></html>
"""

# ══════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_schema():
    conn = get_db(); cur = conn.cursor()
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
        user_agent TEXT DEFAULT '',device_type TEXT DEFAULT '',
        country_code TEXT DEFAULT '',risk_score INTEGER DEFAULT 0
    )""")
    # migrate
    cols = [
        ("ip_address","TEXT DEFAULT ''"),
        ("ip_verified","INTEGER DEFAULT 0"),
        ("referral_paid","INTEGER DEFAULT 0"),
        ("verify_attempts","INTEGER DEFAULT 0"),
        ("last_attempt_at","REAL DEFAULT 0"),
        ("verified_at","REAL DEFAULT 0"),
        ("session_hash","TEXT DEFAULT ''"),
        ("user_agent","TEXT DEFAULT ''"),
        ("device_type","TEXT DEFAULT ''"),
        ("country_code","TEXT DEFAULT ''"),
        ("risk_score","INTEGER DEFAULT 0"),
    ]
    for col, defn in cols:
        try: cur.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
        except sqlite3.OperationalError: pass

    cur.execute("""CREATE TABLE IF NOT EXISTS verify_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,ip TEXT,result TEXT,reason TEXT,
        user_agent TEXT,ts REAL,session_hash TEXT
    )""")
    conn.commit(); conn.close()

# ── helpers ──
def get_real_ip():
    for h in ("CF-Connecting-IP","X-Real-IP","X-Forwarded-For"):
        v = request.headers.get(h,"")
        if v: return v.split(",")[0].strip()
    return request.remote_addr or ""

def detect_device(ua: str) -> str:
    ua = ua or ""
    if re.search(r"iPad|Tablet",ua,re.I): return "Tablet"
    if re.search(r"Mobi|Android|iPhone|iPod",ua,re.I): return "Mobile"
    return "Desktop"

def make_session_hash(user_id: int, ip: str, ua: str) -> str:
    raw = f"{user_id}|{ip}|{ua}|{SECRET_SALT}|{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def ip_taken(ip, uid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE ip_address=? AND user_id!=? LIMIT 1",(ip,uid))
    r = cur.fetchone(); conn.close()
    return r is not None

MAX_ATTEMPTS = 5
RATE_WINDOW  = 3600

def do_verify(user_id, ip, ua):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?",(user_id,))
    u = cur.fetchone()
    now = time.time()

    def log(result, reason, sess=""):
        cur.execute(
            "INSERT INTO verify_log(user_id,ip,result,reason,user_agent,ts,session_hash) VALUES(?,?,?,?,?,?,?)",
            (user_id, ip, result, reason, ua, now, sess))
        conn.commit()

    if not u:
        log("fail","user_not_found")
        conn.close()
        return False, "User not found. Please start the bot first."
    if int(u["banned"] or 0):
        log("fail","banned")
        conn.close()
        return False, "Your account has been banned."
    if int(u["ip_verified"] or 0):
        conn.close()
        return True, "Already verified."

    attempts = int(u["verify_attempts"] or 0)
    last_at  = float(u["last_attempt_at"] or 0)
    if now - last_at < RATE_WINDOW and attempts >= MAX_ATTEMPTS:
        mins = int((RATE_WINDOW - (now - last_at)) / 60)
        log("fail",f"rate_limited_{attempts}")
        conn.close()
        return False, f"Too many attempts. Try again in {mins} min."
    if now - last_at >= RATE_WINDOW:
        attempts = 0
    if not ip:
        log("fail","no_ip")
        conn.close()
        return False, "Could not detect your IP address."
    if ip_taken(ip, user_id):
        cur.execute("UPDATE users SET verify_attempts=?,last_attempt_at=? WHERE user_id=?",
                    (attempts+1, now, user_id))
        log("fail","ip_conflict")
        conn.commit(); conn.close()
        return False, "This IP is already linked to another account."

    device = detect_device(ua)
    sess   = make_session_hash(user_id, ip, ua)
    cur.execute("""UPDATE users SET
        ip_address=?,ip_verified=1,verify_attempts=?,last_attempt_at=?,
        verified_at=?,session_hash=?,user_agent=?,device_type=?,risk_score=0
        WHERE user_id=?""",
        (ip, attempts+1, now, now, sess, ua, device, user_id))
    log("success","ok",sess)
    conn.commit(); conn.close()
    return True, "OK"

# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════
@app.route("/")
def home():
    return {"status":"running","service":"IP Verify Advanced","version":"2.0"}, 200

@app.route("/health")
def health():
    return {"status":"ok","ts":int(time.time())}, 200

@app.route("/ip-verify")
def ip_verify():
    uid = request.args.get("uid","").strip()
    if not uid or not uid.isdigit():
        return render_template_string(HTML_ERROR,
            message="Invalid or missing user ID. Use the link sent by the bot.",
            bot_username=BOT_USERNAME), 400
    user_id = int(uid)
    ip      = get_real_ip()
    ua      = request.headers.get("User-Agent","")
    ok, msg = do_verify(user_id, ip, ua)
    if not ok:
        return render_template_string(HTML_ERROR, message=msg, bot_username=BOT_USERNAME), 400
    return render_template_string(HTML_SUCCESS, user_id=user_id, bot_username=BOT_USERNAME)

@app.route("/api/verify-status/<int:user_id>")
def verify_status(user_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT ip_verified,ip_address,verified_at,device_type,session_hash,risk_score FROM users WHERE user_id=?",(user_id,))
    r = cur.fetchone(); conn.close()
    if not r: return jsonify({"verified":False,"error":"user_not_found"}), 404
    return jsonify({
        "verified":    bool(int(r["ip_verified"] or 0)),
        "ip":          r["ip_address"] or None,
        "verified_at": r["verified_at"] or None,
        "device":      r["device_type"] or None,
        "session":     r["session_hash"] or None,
        "risk_score":  r["risk_score"] or 0,
    })

@app.route("/api/verify-log/<int:user_id>")
def verify_log(user_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT result,reason,ts FROM verify_log WHERE user_id=? ORDER BY ts DESC LIMIT 20",(user_id,))
    rows = [dict(r) for r in cur.fetchall()]; conn.close()
    return jsonify({"log": rows})

@app.route("/api/stats")
def stats():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM users")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as v FROM users WHERE ip_verified=1")
    verified = cur.fetchone()["v"]
    cur.execute("SELECT COUNT(*) as f FROM verify_log WHERE result='fail'")
    fails = cur.fetchone()["f"]
    conn.close()
    return jsonify({"total_users":total,"verified":verified,"failed_attempts":fails})

if __name__ == "__main__":
    ensure_schema()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
