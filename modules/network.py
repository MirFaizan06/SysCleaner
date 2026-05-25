"""Network refresh — DNS flush, Winsock reset, connectivity & adapter info."""
from __future__ import annotations
import socket
import subprocess
import psutil
from rich.console import Console
from rich.table import Table
from rich import box

from modules.utils import human_size, section_header, status_icon


def _run_cmd(cmd: list[str], timeout: int = 15) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def _check_internet(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.create_connection((host, port))
        return True
    except OSError:
        return False


def _get_adapters() -> list[dict]:
    adapters = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    counters = psutil.net_io_counters(pernic=True)

    for name, stat in stats.items():
        if not stat.isup:
            continue
        ipv4 = ""
        for addr in addrs.get(name, []):
            if addr.family == socket.AF_INET:
                ipv4 = addr.address
                break
        cnt = counters.get(name)
        sent     = human_size(cnt.bytes_sent) if cnt else "—"
        received = human_size(cnt.bytes_recv) if cnt else "—"
        adapters.append({"name": name[:28], "ip": ipv4 or "—", "sent": sent, "recv": received})
    return adapters


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    ok_dns, _ = _run_cmd(["ipconfig", "/flushdns"])
    internet   = _check_internet()
    adapters   = _get_adapters()
    return {
        "internet_connected": internet,
        "dns_flushed": ok_dns,
        "adapters": adapters,
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "NETWORK REFRESH")

    ops: list[tuple[str, list[str], bool]] = [
        ("Flush DNS Cache",         ["ipconfig", "/flushdns"],          False),
        ("Re-register DNS",         ["ipconfig", "/registerdns"],       False),
        ("Reset Winsock",           ["netsh", "winsock", "reset"],      True),
        ("Reset TCP/IP Stack",      ["netsh", "int", "ip", "reset"],    True),
    ]

    reboot_needed = False
    for label, cmd, needs_admin in ops:
        if needs_admin and not is_admin:
            console.print(f"  [dim]  {label:<28} — needs Administrator[/]")
            continue
        ok, out = _run_cmd(cmd)
        icon = status_icon(ok)
        msg  = ""
        if "reboot" in out.lower() or "restart" in out.lower():
            msg = "  [yellow](reboot required)[/]"
            reboot_needed = True
        console.print(f"  {icon}  {label:<28}{msg}")

    if reboot_needed:
        console.print("\n  [yellow]Some changes take effect after a reboot.[/]")

    console.print()

    # ── Connectivity ─────────────────────────────────────────────────────────
    internet = _check_internet()
    console.print(f"  {status_icon(internet)}  Internet connectivity")
    console.print()

    # ── Active adapters ───────────────────────────────────────────────────────
    adapters = _get_adapters()
    if adapters:
        tbl = Table(box=box.SIMPLE, header_style="bold cyan", show_header=True, padding=(0, 1))
        tbl.add_column("Adapter",   width=30)
        tbl.add_column("IPv4",      width=16)
        tbl.add_column("Sent",      justify="right", width=10)
        tbl.add_column("Received",  justify="right", width=10)
        for a in adapters:
            tbl.add_row(a["name"], a["ip"], a["sent"], a["recv"])
        console.print(tbl)
    else:
        console.print("  [dim]No active network adapters found.[/]")

    console.print()
