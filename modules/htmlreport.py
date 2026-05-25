"""HTML System Report — generates a self-contained HTML file in ~/Documents."""
from __future__ import annotations
import datetime
import json
import os
import pathlib
import socket
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from modules.utils import section_header, human_size

# ── HTML template ─────────────────────────────────────────────────────────────

_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f8f9fc;--surface:#fff;--surface2:#f1f3f8;--border:#e2e6ef;
  --text:#111827;--text2:#374151;--muted:#6b7280;
  --violet:#7c3aed;--violet-light:#ede9fe;
  --green:#16a34a;--green-bg:#dcfce7;
  --yellow:#ca8a04;--yellow-bg:#fef9c3;
  --red:#dc2626;--red-bg:#fee2e2;
  --cyan:#0891b2;
}
@media(prefers-color-scheme:dark){
  :root{
    --bg:#0d1117;--surface:#161b22;--surface2:#1c2230;--border:#30363d;
    --text:#f0f6fc;--text2:#8b949e;--muted:#484f58;
    --violet:#a78bfa;--violet-light:#1e1535;
    --green:#4ade80;--green-bg:#0d2818;
    --yellow:#fbbf24;--yellow-bg:#1a1505;
    --red:#f87171;--red-bg:#2d0808;
    --cyan:#22d3ee;
  }
}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;font-size:14px}
a{color:var(--violet);text-decoration:none}
/* Header */
header{background:var(--surface);border-bottom:1px solid var(--border);padding:24px 32px;display:flex;align-items:center;gap:20px}
.logo-wrap{width:48px;height:48px;background:var(--violet);border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.logo-wrap svg{width:28px;height:28px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.header-title h1{font-size:20px;font-weight:700;color:var(--text)}
.header-title p{font-size:12px;color:var(--muted);margin-top:2px}
.risk-badge{margin-left:auto;padding:6px 16px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
.risk-low{background:var(--green-bg);color:var(--green)}
.risk-medium{background:var(--yellow-bg);color:var(--yellow)}
.risk-high{background:var(--red-bg);color:var(--red)}
/* Layout */
main{max-width:1100px;margin:0 auto;padding:32px}
section{margin-bottom:40px}
h2{font-size:16px;font-weight:700;color:var(--text);margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
h2 span.dot{width:8px;height:8px;border-radius:50%;background:var(--violet);flex-shrink:0;display:inline-block}
/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin-bottom:32px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px}
.card-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:6px}
.card-value{font-size:22px;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums}
.card-sub{font-size:12px;color:var(--muted);margin-top:4px}
/* Progress bar */
.bar-wrap{margin-top:8px}
.bar-track{height:8px;background:var(--surface2);border-radius:999px;overflow:hidden;margin-bottom:4px}
.bar-fill{height:100%;border-radius:999px;transition:width .3s}
.bar-green{background:var(--green)}
.bar-yellow{background:var(--yellow)}
.bar-red{background:var(--red)}
.bar-label{font-size:11px;color:var(--muted);display:flex;justify-content:space-between}
/* Drive section */
.drives{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.drive-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px}
.drive-name{font-weight:700;font-size:15px;margin-bottom:4px}
.drive-fs{font-size:11px;color:var(--muted);margin-bottom:12px}
/* Tables */
table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden}
thead{background:var(--surface2)}
th{padding:10px 14px;text-align:left;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);white-space:nowrap}
td{padding:10px 14px;font-size:13px;border-top:1px solid var(--border);color:var(--text2)}
tr:hover td{background:var(--surface2)}
/* Badges */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.badge-critical{background:var(--red-bg);color:var(--red)}
.badge-error{background:var(--red-bg);color:var(--red)}
.badge-warning{background:var(--yellow-bg);color:var(--yellow)}
.badge-info{background:var(--violet-light);color:var(--violet)}
.badge-ok{background:var(--green-bg);color:var(--green)}
/* Tips */
.tips-list{display:flex;flex-direction:column;gap:10px}
.tip-item{display:flex;gap:12px;align-items:flex-start;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px}
.tip-icon{font-size:16px;flex-shrink:0;margin-top:1px}
.tip-text{font-size:13px;color:var(--text2);line-height:1.6}
/* Dir list */
.dir-bar-wrap{display:flex;align-items:center;gap:10px}
.dir-bar-track{flex:1;height:8px;background:var(--surface2);border-radius:999px;overflow:hidden}
.dir-bar-fill{height:100%;background:var(--violet);border-radius:999px}
/* Footer */
footer{text-align:center;padding:32px;color:var(--muted);font-size:12px;border-top:1px solid var(--border)}
.status-ok::before{content:"✔ ";color:var(--green)}
.status-bad::before{content:"✘ ";color:var(--red)}
.mono{font-family:ui-monospace,monospace;font-size:12px}
"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SysCleaner Report — {hostname} — {date}</title>
<style>{css}</style>
</head>
<body>
<header>
  <div class="logo-wrap">
    <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
  </div>
  <div class="header-title">
    <h1>System Report</h1>
    <p>{hostname} &nbsp;·&nbsp; {os_name} &nbsp;·&nbsp; Generated {datetime_full}</p>
  </div>
  <div class="risk-badge risk-{risk_class}">{risk_level} risk</div>
</header>
<main>

  <!-- Overview cards -->
  <div class="cards">
    <div class="card">
      <div class="card-label">CPU Usage</div>
      <div class="card-value">{cpu_usage}%</div>
      <div class="card-sub">{cpu_name}</div>
      {cpu_bar}
    </div>
    <div class="card">
      <div class="card-label">RAM Usage</div>
      <div class="card-value">{ram_pct}%</div>
      <div class="card-sub">{ram_used} of {ram_total}</div>
      {ram_bar}
    </div>
    <div class="card">
      <div class="card-label">Uptime</div>
      <div class="card-value">{uptime}</div>
      <div class="card-sub">Since last reboot</div>
    </div>
    <div class="card">
      <div class="card-label">Threat Level</div>
      <div class="card-value" style="text-transform:capitalize">{risk_level}</div>
      <div class="card-sub">{processes_scanned} processes scanned</div>
    </div>
    {battery_card}
  </div>

  <!-- Disk Usage -->
  <section id="disk">
    <h2><span class="dot"></span> Disk Usage</h2>
    <div class="drives">{drive_cards}</div>
  </section>

  <!-- Threat Scan -->
  <section id="threats">
    <h2><span class="dot"></span> Threat Scan</h2>
    {threat_content}
  </section>

  <!-- System Events -->
  <section id="events">
    <h2><span class="dot"></span> Recent System Events</h2>
    {events_content}
  </section>

  <!-- Startup Programs -->
  <section id="startup">
    <h2><span class="dot"></span> Startup Programs</h2>
    {startup_content}
  </section>

  <!-- Tips -->
  <section id="tips">
    <h2><span class="dot"></span> Recommendations</h2>
    <div class="tips-list">{tips_content}</div>
  </section>

</main>
<footer>
  Generated by <strong>SysCleaner</strong> v{version} &nbsp;·&nbsp;
  <a href="https://techbytesdesign.in" target="_blank">Tech Bytes Design</a> &nbsp;·&nbsp;
  Report date: {datetime_full}
</footer>
</body>
</html>"""


# ── Builders ──────────────────────────────────────────────────────────────────

def _bar_html(pct: float, *, label_left: str = "", label_right: str = "") -> str:
    if pct < 60:
        cls = "bar-green"
    elif pct < 85:
        cls = "bar-yellow"
    else:
        cls = "bar-red"
    width = min(100, pct)
    labels = ""
    if label_left or label_right:
        labels = f'<div class="bar-label"><span>{label_left}</span><span>{label_right}</span></div>'
    return (
        f'<div class="bar-wrap">'
        f'<div class="bar-track"><div class="bar-fill {cls}" style="width:{width:.1f}%"></div></div>'
        f'{labels}</div>'
    )


def _drive_cards(drives: list[dict]) -> str:
    cards = []
    for d in drives:
        pct = d.get("percent", 0)
        total = human_size(d.get("total_bytes", 0))
        used  = human_size(d.get("used_bytes",  0))
        free  = human_size(d.get("free_bytes",  0))
        bar   = _bar_html(pct, label_left=f"Used {used}", label_right=f"{free} free")
        cards.append(
            f'<div class="drive-card">'
            f'<div class="drive-name">{d.get("device", "?")}</div>'
            f'<div class="drive-fs">{d.get("fstype", "")} &nbsp;·&nbsp; {total} total</div>'
            f'{bar}'
            f'<div style="font-size:13px;margin-top:8px;font-weight:700">{pct:.1f}% used</div>'
            f'</div>'
        )
    return "".join(cards)


def _threat_html(thr: dict) -> str:
    bad_procs = thr.get("bad_processes", [])
    startup_ct = thr.get("startup_count", 0)
    hosts_susp = thr.get("hosts_suspicious", [])
    susp_ports = thr.get("suspicious_ports", [])

    rows = []
    if not bad_procs:
        rows.append('<tr><td class="status-ok">No malicious processes detected</td></tr>')
    else:
        for p in bad_procs:
            rows.append(f'<tr><td class="status-bad">{p["name"]} (PID {p["pid"]}) — {p["reason"]}</td></tr>')

    if not hosts_susp:
        rows.append('<tr><td class="status-ok">Hosts file is clean</td></tr>')
    else:
        for h in hosts_susp[:5]:
            rows.append(f'<tr><td class="status-bad">Hosts: {h}</td></tr>')

    if not susp_ports:
        rows.append('<tr><td class="status-ok">No suspicious listening ports</td></tr>')
    else:
        for p in susp_ports:
            rows.append(f'<tr><td class="status-bad">Port {p["port"]} — {p["reason"]}</td></tr>')

    startup_note = "⚠ Many startup entries" if startup_ct > 20 else "✔ Startup count normal"
    rows.append(f'<tr><td class="{"status-bad" if startup_ct > 20 else "status-ok"}">'
                f'{startup_note} ({startup_ct} found)</td></tr>')

    return f'<table><thead><tr><th>Result</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'


def _events_html(events: list[dict]) -> str:
    if not events:
        return '<p style="color:var(--muted)">No events found.</p>'
    rows = []
    for ev in events:
        lvl = ev.get("level", "")
        cls = {"Critical": "badge-critical", "Error": "badge-error", "Warning": "badge-warning"}.get(lvl, "badge-info")
        desc = ev.get("description", "")[:120]
        rows.append(
            f'<tr>'
            f'<td class="mono">{ev.get("time","")}</td>'
            f'<td><span class="badge {cls}">{lvl}</span></td>'
            f'<td>{ev.get("source","")[:30]}</td>'
            f'<td style="color:var(--muted)">{desc}</td>'
            f'</tr>'
        )
    header = '<thead><tr><th>Time</th><th>Level</th><th>Source</th><th>Message</th></tr></thead>'
    return f'<table>{header}<tbody>{"".join(rows)}</tbody></table>'


def _startup_html(entries: list[dict]) -> str:
    if not entries:
        return '<p style="color:var(--muted)">No startup entries.</p>'
    rows = []
    for e in entries[:30]:
        status = '<span class="badge badge-ok">ON</span>' if e.get("enabled") else '<span class="badge" style="background:var(--surface2);color:var(--muted)">OFF</span>'
        rows.append(
            f'<tr><td>{status}</td>'
            f'<td style="font-size:11px;color:var(--muted)">{e.get("hive","")}</td>'
            f'<td>{e.get("name","")[:40]}</td>'
            f'<td class="mono" style="color:var(--muted)">{e.get("command","")[:60]}</td></tr>'
        )
    if len(entries) > 30:
        rows.append(f'<tr><td colspan="4" style="color:var(--muted);text-align:center">… and {len(entries)-30} more</td></tr>')
    header = '<thead><tr><th>Status</th><th>Hive</th><th>Name</th><th>Command</th></tr></thead>'
    return f'<table>{header}<tbody>{"".join(rows)}</tbody></table>'


def _tips_html(tips_data: dict) -> str:
    items = tips_data.get("tips", [])
    general = tips_data.get("general", [])
    html_items = []
    icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    for t in items:
        icon = icons.get(t.get("level", "info"), "🔵")
        msg = t.get("message", "").replace("[bold]", "<strong>").replace("[/bold]", "</strong>")
        # Strip Rich markup for HTML
        import re
        msg = re.sub(r'\[.*?\]', '', msg)
        html_items.append(f'<div class="tip-item"><div class="tip-icon">{icon}</div><div class="tip-text">{msg}</div></div>')
    for g in general:
        g_clean = re.sub(r'\[.*?\]', '', g) if __import__('re').search(r'\[', g) else g
        import re
        g_clean = re.sub(r'\[.*?\]', '', g)
        html_items.append(f'<div class="tip-item"><div class="tip-icon">💡</div><div class="tip-text">{g_clean}</div></div>')
    return "".join(html_items) if html_items else '<div class="tip-item"><div class="tip-icon">✅</div><div class="tip-text">Your system looks healthy. No urgent recommendations.</div></div>'


def _battery_card(info: dict) -> str:
    bat = info.get("battery")
    if not bat:
        return ""
    plug = "Plugged in" if bat.get("plugged_in") else "On battery"
    pct = bat.get("percent") or 0
    bar = _bar_html(100 - pct)  # inverted: low battery = high urgency
    return (
        f'<div class="card">'
        f'<div class="card-label">Battery</div>'
        f'<div class="card-value">{pct:.0f}%</div>'
        f'<div class="card-sub">{plug}</div>'
        f'</div>'
    )


# ── Public API ────────────────────────────────────────────────────────────────

def generate(console: Console, is_admin: bool = False) -> pathlib.Path | None:
    """Gather all data and write a self-contained HTML report. Returns the file path."""
    from modules import sysinfo, threats, logs, tips
    try:
        from modules import startup as startup_mod
        from modules import diskanalyzer
    except ImportError:
        startup_mod = None
        diskanalyzer = None

    import re

    results: dict = {}
    with Progress(SpinnerColumn(), TextColumn("[dim]{task.description}[/]"),
                  console=console, transient=True) as prog:

        def _collect(name: str, fn):
            t = prog.add_task(f"Collecting {name}…")
            try:
                results[name] = fn()
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

    info_data    = results.get("info", {})
    threat_data  = results.get("threats", {})
    logs_data    = results.get("logs", {})
    tips_data    = results.get("tips", {})
    startup_data = results.get("startup", {})
    disk_data    = results.get("disk", {})

    # ── CPU ───────────────────────────────────────────────────────────────────
    cpu       = info_data.get("cpu", {})
    cpu_usage = cpu.get("usage_pct", 0)
    cpu_name  = cpu.get("name", "Unknown CPU")
    cpu_bar   = _bar_html(cpu_usage, label_left=f"{cpu.get('cores_phys',0)}C / {cpu.get('cores_logic',0)}T", label_right=f"{cpu_usage:.1f}%")

    # ── RAM ───────────────────────────────────────────────────────────────────
    ram = info_data.get("ram", {})
    ram_pct   = ram.get("percent", 0)
    ram_used  = human_size(ram.get("used_bytes", 0))
    ram_total = human_size(ram.get("total_bytes", 0))
    ram_bar   = _bar_html(ram_pct, label_left=f"Used {ram_used}", label_right=f"Total {ram_total}")

    # ── Drives ────────────────────────────────────────────────────────────────
    drives = disk_data.get("drives", info_data.get("disks", []))

    # ── Risk ──────────────────────────────────────────────────────────────────
    risk = threat_data.get("risk_level", "low")
    risk_class = risk.lower()

    # ── Startup ───────────────────────────────────────────────────────────────
    startup_entries = startup_data.get("entries", [])

    # ── Build HTML ────────────────────────────────────────────────────────────
    now = datetime.datetime.now()
    html = _HTML_TEMPLATE.format(
        css              = _CSS,
        hostname         = info_data.get("hostname", socket.gethostname()),
        os_name          = info_data.get("os", "Windows"),
        date             = now.strftime("%Y-%m-%d"),
        datetime_full    = now.strftime("%B %d, %Y  %H:%M"),
        risk_class       = risk_class,
        risk_level       = risk.capitalize(),
        cpu_usage        = f"{cpu_usage:.1f}",
        cpu_name         = cpu_name[:60],
        cpu_bar          = cpu_bar,
        ram_pct          = f"{ram_pct:.1f}",
        ram_used         = ram_used,
        ram_total        = ram_total,
        ram_bar          = ram_bar,
        uptime           = info_data.get("uptime", "—"),
        processes_scanned= threat_data.get("total_processes", 0),
        battery_card     = _battery_card(info_data),
        drive_cards      = _drive_cards(drives),
        threat_content   = _threat_html(threat_data),
        events_content   = _events_html(logs_data.get("events", [])),
        startup_content  = _startup_html(startup_entries),
        tips_content     = _tips_html(tips_data),
        version          = "1.1.0",
    )

    # ── Save ──────────────────────────────────────────────────────────────────
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
        console.print(f"\n  [bold green]✔[/]  Report saved to:\n")
        console.print(f"      [bold cyan]{path}[/]\n")
        console.print("  [dim]Open in any web browser. Supports light and dark mode.[/]\n")

        # Auto-open
        try:
            os.startfile(str(path))
        except Exception:
            pass
    else:
        console.print("  [red]Failed to generate report.[/]\n")
