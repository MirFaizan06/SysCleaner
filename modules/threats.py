"""Basic threat scan — known-bad processes, startup entries, hosts file, suspicious ports."""
from __future__ import annotations
import os
import subprocess
import winreg
import psutil
from rich.console import Console
from rich.table import Table
from rich import box

from modules.utils import section_header, status_icon


# ── Known threat signatures ───────────────────────────────────────────────────

KNOWN_BAD_PROCESSES: dict[str, str] = {
    "xmrig.exe":        "Crypto miner",
    "minerd.exe":       "Crypto miner",
    "cpuminer.exe":     "Crypto miner",
    "nbminer.exe":      "GPU crypto miner",
    "nanominer.exe":    "Crypto miner",
    "darkcomet.exe":    "Remote Access Trojan",
    "nanocore.exe":     "Remote Access Trojan",
    "njrat.exe":        "Remote Access Trojan",
    "quasar.exe":       "Remote Access Trojan",
    "asyncrat.exe":     "Remote Access Trojan",
    "mimikatz.exe":     "Credential theft tool",
    "pwdump.exe":       "Password dumper",
    "fgdump.exe":       "Password dumper",
    "lazagne.exe":      "Credential harvester",
    "ardamax.exe":      "Keylogger",
    "revealer.exe":     "Keylogger",
    "netcat.exe":       "Network backdoor tool",
    "nc.exe":           "Network backdoor tool",
    "cryptolocker.exe": "Ransomware",
    "wannacry.exe":     "Ransomware",
    "wncry.exe":        "Ransomware",
}

SUSPICIOUS_PORTS = {
    1080:  "SOCKS proxy / malware C2",
    4444:  "Metasploit default listener",
    5555:  "Android debug / RAT",
    6666:  "IRC / trojan",
    6667:  "IRC / trojan",
    7777:  "Possible RAT",
    8888:  "Possible RAT / miner",
    31337: "Back Orifice backdoor",
    12345: "NetBus RAT",
}

STARTUP_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
]

HOSTS_PATH   = r"C:\Windows\System32\drivers\etc\hosts"
TRUSTED_NETS = {"127.0.0.1", "::1", "0.0.0.0", "fe80"}


# ── Checks ────────────────────────────────────────────────────────────────────

def _check_processes() -> tuple[list[dict], int]:
    bad: list[dict] = []
    total = 0
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            name  = (proc.info["name"] or "").lower()
            total += 1
            if name in KNOWN_BAD_PROCESSES:
                bad.append({
                    "pid":    proc.info["pid"],
                    "name":   proc.info["name"],
                    "reason": KNOWN_BAD_PROCESSES[name],
                    "path":   proc.info["exe"] or "",
                })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    return bad, total


def _check_startup() -> list[dict]:
    entries: list[dict] = []
    for hive, key_path in STARTUP_KEYS:
        hive_name = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
        try:
            key = winreg.OpenKey(hive, key_path)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    entries.append({"hive": hive_name, "name": name, "command": value[:100]})
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            pass

    startup_folder = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup",
    )
    if os.path.isdir(startup_folder):
        for f in os.listdir(startup_folder):
            entries.append({"hive": "Folder", "name": f, "command": ""})

    return entries


def _check_hosts() -> list[str]:
    suspicious: list[str] = []
    try:
        with open(HOSTS_PATH, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                ip, *hosts = parts
                if any(ip.startswith(t) for t in TRUSTED_NETS):
                    continue
                suspicious.append(f"{ip}  →  {' '.join(hosts)}")
    except OSError:
        pass
    return suspicious


def _check_open_ports() -> list[dict]:
    """Use netstat -ano instead of psutil.net_connections (works without admin, no psutil bugs)."""
    flagged: list[dict] = []
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
        seen: set[int] = set()
        for line in result.stdout.splitlines():
            parts = line.split()
            # netstat -ano columns: Proto  LocalAddr  ForeignAddr  State  PID
            if len(parts) < 4:
                continue
            state = parts[3].upper() if len(parts) >= 4 else ""
            if "LISTEN" not in state:
                continue
            local = parts[1]
            try:
                port = int(local.rsplit(":", 1)[-1])
            except (ValueError, IndexError):
                continue
            if port not in SUSPICIOUS_PORTS or port in seen:
                continue
            seen.add(port)
            pid_str = parts[4] if len(parts) >= 5 else "0"
            pid     = int(pid_str) if pid_str.isdigit() else 0
            name    = ""
            try:
                if pid:
                    name = psutil.Process(pid).name()
            except (psutil.AccessDenied, psutil.NoSuchProcess, ValueError):
                pass
            flagged.append({
                "port":   port,
                "reason": SUSPICIOUS_PORTS[port],
                "pid":    pid,
                "name":   name,
            })
    except Exception:
        pass
    return flagged


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    bad_procs,  total_procs = _check_processes()
    startup                  = _check_startup()
    hosts_suspicious         = _check_hosts()
    open_ports               = _check_open_ports()

    risk = "low"
    if bad_procs or hosts_suspicious or open_ports:
        risk = "high"
    elif len(startup) > 20:
        risk = "medium"

    return {
        "risk_level":          risk,
        "total_processes":     total_procs,
        "bad_processes":       bad_procs,
        "startup_count":       len(startup),
        "startup_entries":     startup,
        "hosts_suspicious":    hosts_suspicious,
        "suspicious_ports":    open_ports,
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "THREAT SCAN", "processes · startup · hosts · ports")

    # ── Processes ─────────────────────────────────────────────────────────────
    console.print("  [bold]Running processes[/]")
    bad_procs, total_procs = _check_processes()
    if bad_procs:
        tbl = Table(box=box.SIMPLE, header_style="bold red", padding=(0, 1))
        tbl.add_column("PID",    width=7,  justify="right")
        tbl.add_column("Name",   width=22)
        tbl.add_column("Reason", width=28)
        tbl.add_column("Path",   width=40, style="dim")
        for p in bad_procs:
            tbl.add_row(str(p["pid"]), f"[red]{p['name']}[/]",
                        p["reason"], p["path"])
        console.print(tbl)
    else:
        console.print(f"  {status_icon(True)}  No known-bad processes detected  "
                      f"[dim]({total_procs} scanned)[/]")

    console.print()

    # ── Startup ───────────────────────────────────────────────────────────────
    startup = _check_startup()
    count   = len(startup)
    icon    = status_icon(count <= 15)
    note    = f"[yellow]  ({count} entries — consider trimming)[/]" if count > 15 else ""
    console.print(f"  [bold]Startup programs[/]")
    console.print(f"  {icon}  {count} startup entries found{note}")

    if startup:
        tbl2 = Table(box=box.SIMPLE, header_style="bold cyan", show_header=True, padding=(0, 1))
        tbl2.add_column("Hive",    width=6,  style="dim")
        tbl2.add_column("Name",    width=32)
        tbl2.add_column("Command", width=55, style="dim")
        for s in startup[:25]:
            tbl2.add_row(s["hive"], s["name"][:32], s["command"][:55])
        if len(startup) > 25:
            tbl2.add_row("…", f"[dim]+{len(startup)-25} more[/]", "")
        console.print(tbl2)

    console.print()

    # ── Hosts file ────────────────────────────────────────────────────────────
    console.print("  [bold]Hosts file[/]")
    suspicious_hosts = _check_hosts()
    if suspicious_hosts:
        console.print(f"  {status_icon(False)}  [red]{len(suspicious_hosts)} non-standard entries[/]")
        for entry in suspicious_hosts[:10]:
            console.print(f"    [red]•[/] {entry}")
    else:
        console.print(f"  {status_icon(True)}  Hosts file looks clean")

    console.print()

    # ── Ports ─────────────────────────────────────────────────────────────────
    console.print("  [bold]Listening ports[/]")
    flagged_ports = _check_open_ports()
    if flagged_ports:
        console.print(f"  {status_icon(False)}  [yellow]{len(flagged_ports)} suspicious port(s) open[/]")
        for p in flagged_ports:
            name = f" ({p['name']})" if p["name"] else ""
            console.print(f"    [yellow]•[/] Port {p['port']}{name} — {p['reason']}")
    else:
        console.print(f"  {status_icon(True)}  No known-suspicious listening ports")

    console.print()

    # ── Summary ───────────────────────────────────────────────────────────────
    threats_found = len(bad_procs) + len(suspicious_hosts) + len(flagged_ports)
    if threats_found:
        console.print(
            f"  [bold red]⚠  {threats_found} potential issue(s) found.[/]  "
            "[dim]This is a basic heuristic scan — not a replacement for antivirus.[/]"
        )
    else:
        console.print(
            f"  [bold green]✔  No obvious threats detected.[/]  "
            "[dim]Always keep Windows Defender active for real-time protection.[/]"
        )

    console.print()
