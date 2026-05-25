"""HTML System Report — generates a beautiful, chart-rich HTML report in ~/Documents."""
from __future__ import annotations
import datetime
import json
import os
import pathlib
import re
import socket
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from modules.utils import section_header, human_size

# ── HTML template ─────────────────────────────────────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="auto">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SysCleaner Report — __HOSTNAME__ — __DATE__</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
/* ── Reset & base ─────────────────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f4f6fb;
  --surface:#ffffff;
  --surface2:#f0f2f8;
  --border:#e2e6ef;
  --text:#0f172a;
  --text2:#475569;
  --muted:#94a3b8;
  --violet:#7c3aed;
  --violet-dim:#ede9fe;
  --violet-glow:rgba(124,58,237,.12);
  --green:#16a34a;--green-bg:#dcfce7;--green-dim:#86efac;
  --yellow:#ca8a04;--yellow-bg:#fef9c3;--yellow-dim:#fde047;
  --red:#dc2626;--red-bg:#fee2e2;--red-dim:#fca5a5;
  --cyan:#0891b2;
  --radius:14px;
  --shadow:0 1px 3px rgba(0,0,0,.06),0 4px 16px rgba(0,0,0,.06);
}
@media(prefers-color-scheme:dark){
  :root{
    --bg:#0b0f1a;
    --surface:#111827;
    --surface2:#1a2235;
    --border:#1e2d45;
    --text:#f1f5f9;
    --text2:#94a3b8;
    --muted:#475569;
    --violet:#a78bfa;
    --violet-dim:#1e1535;
    --violet-glow:rgba(167,139,250,.10);
    --green:#4ade80;--green-bg:#0f2419;--green-dim:#166534;
    --yellow:#fbbf24;--yellow-bg:#1c1400;--yellow-dim:#854d0e;
    --red:#f87171;--red-bg:#250a0a;--red-dim:#7f1d1d;
    --shadow:0 1px 3px rgba(0,0,0,.3),0 4px 20px rgba(0,0,0,.25);
  }
}
html{scroll-behavior:smooth}
body{
  font-family:system-ui,-apple-system,'Segoe UI',sans-serif;
  background:var(--bg);color:var(--text);
  font-size:14px;line-height:1.6;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--violet);text-decoration:none}

/* ── Header ──────────────────────────────────────────────────────────────── */
header{
  background:linear-gradient(135deg,#4c1d95 0%,#6d28d9 50%,#7c3aed 100%);
  padding:0 40px;
  position:sticky;top:0;z-index:100;
  box-shadow:0 2px 16px rgba(109,40,217,.35);
}
.header-inner{
  max-width:1200px;margin:0 auto;
  display:flex;align-items:center;gap:20px;
  padding:18px 0;
}
.logo-mark{
  width:44px;height:44px;background:rgba(255,255,255,.15);
  border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;
  backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.2);
}
.logo-mark svg{width:24px;height:24px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.header-title{flex:1}
.header-title h1{font-size:18px;font-weight:700;color:#fff;letter-spacing:-.01em}
.header-title p{font-size:12px;color:rgba(255,255,255,.65);margin-top:2px}
.risk-pill{
  padding:7px 18px;border-radius:999px;font-size:12px;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;border:1px solid rgba(255,255,255,.25);
  backdrop-filter:blur(8px);
}
.risk-low{background:rgba(74,222,128,.2);color:#bbf7d0}
.risk-medium{background:rgba(251,191,36,.2);color:#fde68a}
.risk-high{background:rgba(248,113,113,.2);color:#fecaca}

/* ── Nav ─────────────────────────────────────────────────────────────────── */
nav{
  background:var(--surface);border-bottom:1px solid var(--border);
  position:sticky;top:80px;z-index:90;
}
.nav-inner{
  max-width:1200px;margin:0 auto;
  display:flex;gap:2px;padding:0 40px;
  overflow-x:auto;scrollbar-width:none;
}
.nav-inner::-webkit-scrollbar{display:none}
.nav-link{
  padding:14px 18px;font-size:13px;font-weight:500;color:var(--text2);
  white-space:nowrap;border-bottom:2px solid transparent;
  transition:color .15s,border-color .15s;
}
.nav-link:hover,.nav-link.active{color:var(--violet);border-bottom-color:var(--violet)}

/* ── Main ────────────────────────────────────────────────────────────────── */
main{max-width:1200px;margin:0 auto;padding:36px 40px 80px}
section{margin-bottom:48px;scroll-margin-top:140px}
.section-title{
  font-size:15px;font-weight:700;color:var(--text);
  margin-bottom:20px;display:flex;align-items:center;gap:10px;
}
.section-title::before{
  content:'';width:4px;height:18px;background:var(--violet);
  border-radius:999px;flex-shrink:0;
}

/* ── Stat cards ──────────────────────────────────────────────────────────── */
.stat-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:16px;margin-bottom:32px;
}
.stat-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;
  box-shadow:var(--shadow);
  display:flex;flex-direction:column;gap:4px;
}
.stat-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.stat-value{font-size:26px;font-weight:800;color:var(--text);line-height:1.1;font-variant-numeric:tabular-nums}
.stat-sub{font-size:12px;color:var(--text2);margin-top:2px}
.stat-bar{margin-top:12px}
.bar-track{height:6px;background:var(--surface2);border-radius:999px;overflow:hidden}
.bar-fill{height:100%;border-radius:999px;transition:width 1s cubic-bezier(.4,0,.2,1)}
.bar-green{background:var(--green)}
.bar-yellow{background:var(--yellow)}
.bar-red{background:var(--red)}

/* ── Gauge cards ─────────────────────────────────────────────────────────── */
.gauge-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
  gap:16px;margin-bottom:32px;
}
.gauge-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);
  display:flex;flex-direction:column;align-items:center;text-align:center;gap:4px;
}
.gauge-wrap{position:relative;width:140px;height:80px;margin-bottom:8px}
.gauge-wrap canvas{position:absolute;top:0;left:0}
.gauge-center{
  position:absolute;bottom:0;left:0;right:0;
  font-size:20px;font-weight:800;color:var(--text);
  text-align:center;line-height:1;
}
.gauge-label{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.gauge-sub{font-size:12px;color:var(--text2)}

/* ── Disk section ────────────────────────────────────────────────────────── */
.disk-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:20px;
}
@media(max-width:760px){.disk-grid{grid-template-columns:1fr}}
.chart-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);
}
.chart-card h3{font-size:13px;font-weight:700;color:var(--text);margin-bottom:20px}
.drive-donuts{display:flex;flex-wrap:wrap;gap:24px;justify-content:center}
.drive-donut{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}
.drive-donut canvas{width:100px!important;height:100px!important}
.drive-name{font-size:12px;font-weight:700;color:var(--text)}
.drive-info{font-size:11px;color:var(--text2);line-height:1.4}

/* ── Tables ──────────────────────────────────────────────────────────────── */
.table-wrap{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);
}
table{width:100%;border-collapse:collapse}
thead{background:var(--surface2)}
th{
  padding:12px 16px;text-align:left;
  font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
  white-space:nowrap;
}
td{
  padding:11px 16px;font-size:13px;border-top:1px solid var(--border);color:var(--text2);
}
tr:hover td{background:var(--surface2)}
.mono{font-family:ui-monospace,monospace;font-size:12px}

/* ── Badges ──────────────────────────────────────────────────────────────── */
.badge{
  display:inline-flex;align-items:center;gap:4px;
  padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;
}
.badge-critical,.badge-error{background:var(--red-bg);color:var(--red)}
.badge-warning{background:var(--yellow-bg);color:var(--yellow)}
.badge-info{background:var(--violet-dim);color:var(--violet)}
.badge-ok{background:var(--green-bg);color:var(--green)}
.badge-off{background:var(--surface2);color:var(--muted)}

/* ── Status cards (threats) ──────────────────────────────────────────────── */
.status-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
  gap:14px;
}
.status-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px;box-shadow:var(--shadow);
  display:flex;align-items:flex-start;gap:14px;
}
.status-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px}
.status-ok-icon{background:var(--green-bg)}
.status-warn-icon{background:var(--yellow-bg)}
.status-bad-icon{background:var(--red-bg)}
.status-body{}
.status-title{font-size:13px;font-weight:700;color:var(--text);margin-bottom:2px}
.status-desc{font-size:12px;color:var(--text2);line-height:1.5}

/* ── Tips ────────────────────────────────────────────────────────────────── */
.tips-list{display:flex;flex-direction:column;gap:10px}
.tip-item{
  background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:16px 20px;box-shadow:var(--shadow);
  display:flex;align-items:flex-start;gap:14px;
}
.tip-item.tip-critical{border-left:3px solid var(--red)}
.tip-item.tip-warning{border-left:3px solid var(--yellow)}
.tip-item.tip-info{border-left:3px solid var(--violet)}
.tip-icon{font-size:20px;flex-shrink:0;margin-top:1px}
.tip-text{font-size:13px;color:var(--text2);line-height:1.7}
.tip-text strong{color:var(--text)}

/* ── System info overview table ──────────────────────────────────────────── */
.info-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:16px;
}
.info-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);
}
.info-card h3{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-bottom:12px}
.info-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:13px}
.info-row:last-child{border-bottom:none}
.info-key{color:var(--text2)}
.info-val{font-weight:600;color:var(--text);text-align:right;max-width:60%}

/* ── Footer ──────────────────────────────────────────────────────────────── */
footer{
  background:var(--surface);border-top:1px solid var(--border);
  text-align:center;padding:28px 40px;
  color:var(--muted);font-size:12px;line-height:2;
}
footer strong{color:var(--text)}

/* ── Animations ──────────────────────────────────────────────────────────── */
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
section{animation:fadeUp .5s ease both}
section:nth-child(2){animation-delay:.05s}
section:nth-child(3){animation-delay:.10s}
section:nth-child(4){animation-delay:.15s}
section:nth-child(5){animation-delay:.20s}
section:nth-child(6){animation-delay:.25s}
section:nth-child(7){animation-delay:.30s}
</style>
</head>
<body>

<!-- Header -->
<header>
  <div class="header-inner">
    <div class="logo-mark">
      <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
    </div>
    <div class="header-title">
      <h1>SysCleaner — System Report</h1>
      <p id="header-sub">Loading…</p>
    </div>
    <div class="risk-pill risk-__RISK_CLASS__" id="risk-pill">__RISK_LABEL__</div>
  </div>
</header>

<!-- Nav -->
<nav>
  <div class="nav-inner">
    <a class="nav-link active" href="#overview">Overview</a>
    <a class="nav-link" href="#disk">Disk</a>
    <a class="nav-link" href="#security">Security</a>
    <a class="nav-link" href="#events">Events</a>
    <a class="nav-link" href="#startup">Startup</a>
    <a class="nav-link" href="#tips">Tips</a>
  </div>
</nav>

<main>

<!-- Overview -->
<section id="overview">
  <div class="section-title">System Overview</div>

  <div class="gauge-grid" id="gauge-grid">
    <!-- Filled by JS -->
  </div>

  <div class="info-grid" id="info-grid">
    <!-- Filled by JS -->
  </div>
</section>

<!-- Disk -->
<section id="disk">
  <div class="section-title">Disk Usage</div>
  <div class="disk-grid">
    <div class="chart-card">
      <h3>Drives</h3>
      <div class="drive-donuts" id="drive-donuts"></div>
    </div>
    <div class="chart-card">
      <h3>Top Folders by Size</h3>
      <canvas id="dirsChart" style="max-height:280px"></canvas>
    </div>
  </div>
</section>

<!-- Security -->
<section id="security">
  <div class="section-title">Security Scan</div>
  <div class="status-grid" id="security-grid"></div>
</section>

<!-- Events -->
<section id="events">
  <div class="section-title">Recent System Events</div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Time</th><th>Level</th><th>Source</th><th>ID</th><th>Message</th></tr></thead>
      <tbody id="events-body"></tbody>
    </table>
  </div>
</section>

<!-- Startup -->
<section id="startup">
  <div class="section-title">Startup Programs</div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Status</th><th>Source</th><th>Name</th><th>Command</th></tr></thead>
      <tbody id="startup-body"></tbody>
    </table>
  </div>
</section>

<!-- Tips -->
<section id="tips">
  <div class="section-title">Recommendations</div>
  <div class="tips-list" id="tips-list"></div>
</section>

</main>

<footer>
  Generated by <strong>SysCleaner v__VERSION__</strong> &nbsp;·&nbsp;
  <a href="https://techbytesdesign.in">Tech Bytes Design</a>
  &nbsp;·&nbsp; __DATETIME__
</footer>

<script>
// ── Report data injected by Python ─────────────────────────────────────────
const R = __REPORT_JSON__;

// ── Helpers ────────────────────────────────────────────────────────────────
const qs = id => document.getElementById(id);
function pctColor(p){return p<60?'#22c55e':p<85?'#eab308':'#ef4444'}
function humanBytes(b){
  const u=['B','KB','MB','GB','TB'];let i=0;
  while(Math.abs(b)>=1024&&i<u.length-1){b/=1024;i++}
  return b.toFixed(1)+' '+u[i];
}
function stripRich(s){return s.replace(/\[.*?\]/g,'').replace(/\[\//g,'').trim()}

// ── Chart.js defaults ──────────────────────────────────────────────────────
const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
Chart.defaults.color = isDark ? '#94a3b8' : '#64748b';
Chart.defaults.font.family = "system-ui,-apple-system,'Segoe UI',sans-serif";

// ── Header ─────────────────────────────────────────────────────────────────
qs('header-sub').textContent =
  (R.info.hostname||'') + '  ·  ' + (R.info.os||'') + '  ·  Generated __DATETIME__';

// ── Gauge cards ────────────────────────────────────────────────────────────
function makeGauge(container, pct, label, sub){
  const card = document.createElement('div');
  card.className = 'gauge-card';
  const cid = 'g_' + Math.random().toString(36).slice(2);
  card.innerHTML = `
    <div class="gauge-wrap">
      <canvas id="${cid}" width="140" height="80"></canvas>
      <div class="gauge-center">${pct.toFixed(0)}<span style="font-size:14px;font-weight:600">%</span></div>
    </div>
    <div class="gauge-label">${label}</div>
    <div class="gauge-sub">${sub}</div>`;
  container.appendChild(card);
  const color = pctColor(pct);
  const bg = isDark ? '#1e2d45' : '#f1f5f9';
  new Chart(document.getElementById(cid), {
    type:'doughnut',
    data:{datasets:[{
      data:[pct, 100-pct],
      backgroundColor:[color, bg],
      borderWidth:0,circumference:180,rotation:-90,
    }]},
    options:{
      cutout:'72%',plugins:{legend:{display:false},tooltip:{enabled:false}},
      animation:{duration:1200,easing:'easeInOutQuart'},
    }
  });
}

const g = qs('gauge-grid');
const cpu = R.info.cpu||{};
const ram = R.info.ram||{};
makeGauge(g, cpu.usage_pct||0, 'CPU Usage',
  (cpu.name||'CPU').split('@')[0].trim().slice(0,40) + ' · ' + (cpu.cores_phys||0) + 'C / ' + (cpu.cores_logic||0) + 'T');
makeGauge(g, ram.percent||0, 'RAM Usage',
  humanBytes(ram.used_bytes||0) + ' used of ' + humanBytes(ram.total_bytes||0));

(R.info.disks||[]).forEach(d=>{
  makeGauge(g, d.percent||0, d.device||'Disk',
    humanBytes(d.free_bytes||0) + ' free of ' + humanBytes(d.total_bytes||0));
});

if(R.info.battery){
  const bat = R.info.battery;
  const plug = bat.plugged_in ? '⚡ Plugged in' : '🔋 On battery';
  const card = document.createElement('div');
  card.className = 'gauge-card';
  card.innerHTML = `
    <div style="font-size:36px;margin-bottom:8px">${bat.percent>=70?'🔋':bat.percent>=30?'🪫':'❗'}</div>
    <div class="gauge-label">Battery</div>
    <div class="stat-value" style="font-size:26px;font-weight:800">${(bat.percent||0).toFixed(0)}%</div>
    <div class="gauge-sub">${plug}</div>`;
  g.appendChild(card);
}

// ── System info cards ──────────────────────────────────────────────────────
const ig = qs('info-grid');
function infoCard(title, rows){
  const c = document.createElement('div');
  c.className = 'info-card';
  c.innerHTML = `<h3>${title}</h3>` +
    rows.map(([k,v])=>`<div class="info-row"><span class="info-key">${k}</span><span class="info-val">${v}</span></div>`).join('');
  ig.appendChild(c);
}

infoCard('System', [
  ['OS', R.info.os||'—'],
  ['Hostname', R.info.hostname||'—'],
  ['Uptime', R.info.uptime||'—'],
]);

if(cpu.name){
  infoCard('Processor', [
    ['Model', (cpu.name||'').split('@')[0].trim()],
    ['Cores', (cpu.cores_phys||0) + ' Physical / ' + (cpu.cores_logic||0) + ' Logical'],
    ['Frequency', cpu.freq_mhz ? cpu.freq_mhz + ' MHz' : '—'],
    ['Usage', (cpu.usage_pct||0).toFixed(1) + '%'],
  ]);
}

infoCard('Memory', [
  ['Total', humanBytes(ram.total_bytes||0)],
  ['Used', humanBytes(ram.used_bytes||0)],
  ['Free', humanBytes(ram.free_bytes||0)],
  ['Usage', (ram.percent||0).toFixed(1) + '%'],
]);

// ── Drive donuts ────────────────────────────────────────────────────────────
const dd = qs('drive-donuts');
(R.info.disks||[]).forEach(d=>{
  const cid = 'dr_'+Math.random().toString(36).slice(2);
  const wrap = document.createElement('div');
  wrap.className = 'drive-donut';
  const pct = d.percent||0;
  wrap.innerHTML = `
    <canvas id="${cid}"></canvas>
    <div class="drive-name">${d.device||'?'}</div>
    <div class="drive-info">${humanBytes(d.used_bytes||0)} / ${humanBytes(d.total_bytes||0)}<br>${pct.toFixed(1)}% used</div>`;
  dd.appendChild(wrap);
  const color = pctColor(pct);
  const bg = isDark ? '#1e2d45' : '#f1f5f9';
  new Chart(document.getElementById(cid), {
    type:'doughnut',
    data:{datasets:[{data:[pct,100-pct],backgroundColor:[color,bg],borderWidth:0}]},
    options:{cutout:'65%',plugins:{legend:{display:false},tooltip:{enabled:false}},animation:{duration:1000}},
  });
});

// ── Top dirs bar chart ──────────────────────────────────────────────────────
const dirs = (R.disk&&R.disk.top_dirs||[]).slice(0,10);
if(dirs.length){
  const labels = dirs.map(d=>d.label||d.path.split(/[/\\]/).pop());
  const values = dirs.map(d=>+(d.bytes/1073741824).toFixed(2));
  new Chart(qs('dirsChart'), {
    type:'bar',
    data:{
      labels,
      datasets:[{
        data:values,
        backgroundColor: values.map((_,i)=>`hsl(${260+i*8},70%,${isDark?55:50}%)`),
        borderRadius:6,
        borderSkipped:false,
      }]
    },
    options:{
      indexAxis:'y',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>' '+ctx.parsed.x.toFixed(2)+' GB'}}},
      scales:{
        x:{grid:{color:isDark?'#1e2d45':'#e2e6ef'},ticks:{callback:v=>v+' GB'}},
        y:{grid:{display:false},ticks:{font:{size:11}}},
      },
      animation:{duration:1000,easing:'easeInOutQuart'},
    }
  });
}

// ── Security status cards ───────────────────────────────────────────────────
const thr = R.threats||{};
const sg = qs('security-grid');
function secCard(icon, iconClass, title, desc){
  const c = document.createElement('div');
  c.className = 'status-card';
  c.innerHTML = `
    <div class="status-icon ${iconClass}">${icon}</div>
    <div class="status-body">
      <div class="status-title">${title}</div>
      <div class="status-desc">${desc}</div>
    </div>`;
  sg.appendChild(c);
}

const badP = thr.bad_processes||[];
secCard(
  badP.length?'⚠️':'✅',
  badP.length?'status-bad-icon':'status-ok-icon',
  'Processes',
  badP.length
    ? badP.map(p=>`<strong>${p.name}</strong> (PID ${p.pid}) — ${p.reason}`).join('<br>')
    : `No malicious processes found out of ${thr.total_processes||0} scanned`
);

const hosts = thr.hosts_suspicious||[];
secCard(
  hosts.length?'⚠️':'✅',
  hosts.length?'status-bad-icon':'status-ok-icon',
  'Hosts File',
  hosts.length
    ? hosts.slice(0,3).map(h=>`<code>${h}</code>`).join('<br>')
    : 'No suspicious redirects found in hosts file'
);

const ports = thr.suspicious_ports||[];
secCard(
  ports.length?'⚠️':'✅',
  ports.length?'status-warn-icon':'status-ok-icon',
  'Network Ports',
  ports.length
    ? ports.map(p=>`Port <strong>${p.port}</strong> — ${p.reason}`).join('<br>')
    : 'No suspicious listening ports detected'
);

const sc = thr.startup_count||0;
secCard(
  sc>20?'⚠️':'✅',
  sc>20?'status-warn-icon':'status-ok-icon',
  'Startup Programs',
  sc>20 ? `${sc} startup entries — more than recommended. Use Startup Manager to trim.`
         : `${sc} startup entries — within normal range`
);

// ── Events table ────────────────────────────────────────────────────────────
const eb = qs('events-body');
const events = (R.logs&&R.logs.events)||[];
if(!events.length){
  eb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px">No events found</td></tr>';
}else{
  events.forEach(ev=>{
    const lvl = ev.level||'';
    const cls = {Critical:'badge-critical',Error:'badge-error',Warning:'badge-warning'}[lvl]||'badge-info';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="mono">${ev.time||''}</td>
      <td><span class="badge ${cls}">${lvl}</span></td>
      <td>${(ev.source||'').slice(0,32)}</td>
      <td class="mono">${ev.event_id||''}</td>
      <td style="color:var(--muted);max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${(ev.description||'').slice(0,100)}</td>`;
    eb.appendChild(tr);
  });
}

// ── Startup table ───────────────────────────────────────────────────────────
const sb = qs('startup-body');
const entries = (R.startup&&R.startup.entries)||[];
if(!entries.length){
  sb.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:24px">No startup entries found</td></tr>';
}else{
  entries.slice(0,40).forEach(e=>{
    const on = e.enabled;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="badge ${on?'badge-ok':'badge-off'}">${on?'ON':'OFF'}</span></td>
      <td class="mono" style="color:var(--muted)">${e.hive||''}</td>
      <td style="font-weight:${on?600:400};color:${on?'var(--text)':'var(--muted)'}">${(e.name||'').slice(0,40)}</td>
      <td class="mono" style="color:var(--muted);font-size:11px">${(e.command||'').slice(0,60)}</td>`;
    sb.appendChild(tr);
  });
  if(entries.length>40){
    sb.innerHTML += `<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:12px">… and ${entries.length-40} more</td></tr>`;
  }
}

// ── Tips ─────────────────────────────────────────────────────────────────────
const tl = qs('tips-list');
const tips = [...((R.tips&&R.tips.tips)||[]),...((R.tips&&R.tips.general)||[]).map(m=>({level:'info',message:m}))];
const icons = {critical:'🔴',warning:'🟡',info:'💡'};
if(!tips.length){
  tl.innerHTML = '<div class="tip-item tip-info"><div class="tip-icon">✅</div><div class="tip-text">Your system looks healthy. No urgent recommendations.</div></div>';
}else{
  tips.forEach(t=>{
    const d = document.createElement('div');
    d.className = `tip-item tip-${t.level||'info'}`;
    d.innerHTML = `<div class="tip-icon">${icons[t.level]||'💡'}</div><div class="tip-text">${stripRich(t.message||t||'')}</div>`;
    tl.appendChild(d);
  });
}

// ── Sticky nav highlight ─────────────────────────────────────────────────────
const sections = document.querySelectorAll('main section[id]');
const navLinks  = document.querySelectorAll('.nav-link');
const observer  = new IntersectionObserver(entries=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      navLinks.forEach(l=>l.classList.toggle('active', l.getAttribute('href')==='#'+e.target.id));
    }
  });
},{threshold:.25,rootMargin:'-100px 0px -60% 0px'});
sections.forEach(s=>observer.observe(s));
</script>
</body>
</html>"""


# ── Strip Rich markup from text ───────────────────────────────────────────────

def _strip_rich(s: str) -> str:
    return re.sub(r'\[/?[^\]]*\]', '', s).strip()


def _strip_rich_dict(obj):
    """Recursively strip Rich markup from all string values."""
    if isinstance(obj, str):
        return _strip_rich(obj)
    if isinstance(obj, dict):
        return {k: _strip_rich_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_rich_dict(v) for v in obj]
    return obj


# ── Public API ────────────────────────────────────────────────────────────────

def generate(console: Console, is_admin: bool = False) -> pathlib.Path | None:
    from modules import sysinfo, threats, logs, tips

    try:
        from modules import startup as startup_mod
    except ImportError:
        startup_mod = None
    try:
        from modules import diskanalyzer
    except ImportError:
        diskanalyzer = None

    results: dict = {}

    with Progress(SpinnerColumn(), TextColumn("[dim]{task.description}[/]"),
                  console=console, transient=True) as prog:

        def _collect(name: str, fn):
            t = prog.add_task(f"Collecting {name}…")
            try:
                results[name] = _strip_rich_dict(fn())
            except Exception as exc:
                results[name] = {"error": str(exc)}
            prog.remove_task(t)

        _collect("info",    lambda: sysinfo.report(is_admin))
        _collect("threats", lambda: threats.report(is_admin))
        _collect("logs",    lambda: logs.report(is_admin))
        _collect("tips",    lambda: tips.report(is_admin))
        if startup_mod:
            _collect("startup", lambda: startup_mod.report(is_admin))
        if diskanalyzer:
            _collect("disk",    lambda: diskanalyzer.report(is_admin))

    # Determine risk badge
    thr = results.get("threats", {})
    risk = thr.get("risk_level", "low")

    now = datetime.datetime.now()
    date_str     = now.strftime("%Y-%m-%d")
    datetime_str = now.strftime("%B %d, %Y  %H:%M")

    report_json = json.dumps(results, indent=None, default=str, ensure_ascii=False)

    html = (
        _HTML
        .replace("__HOSTNAME__",    results.get("info", {}).get("hostname", socket.gethostname()))
        .replace("__DATE__",        date_str)
        .replace("__DATETIME__",    datetime_str)
        .replace("__RISK_CLASS__",  risk.lower())
        .replace("__RISK_LABEL__",  risk.upper() + " RISK")
        .replace("__REPORT_JSON__", report_json)
        .replace("__VERSION__",     "1.1.0")
    )

    reports_dir = pathlib.Path.home() / "Documents" / "SysCleaner Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"SysCleaner_Report_{now.strftime('%Y-%m-%d_%H-%M-%S')}.html"
    path = reports_dir / filename
    path.write_text(html, encoding="utf-8")
    return path


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "HTML REPORT", "full system snapshot saved to Documents")
    console.print("  [dim]Collecting system data from all modules…[/]\n")

    path = generate(console, is_admin)
    if path:
        console.print(f"\n  [bold green]✔[/]  Saved to:\n")
        console.print(f"      [bold cyan]{path}[/]\n")
        console.print(
            "  [dim]Opens in any browser. Light/dark mode auto. "
            "Charts require internet for Chart.js.[/]\n"
        )
        try:
            os.startfile(str(path))
        except Exception:
            pass
    else:
        console.print("  [red]Failed to generate report.[/]\n")
