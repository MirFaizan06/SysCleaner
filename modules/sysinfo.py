"""System information — OS, CPU, RAM, disks, uptime, battery."""
from __future__ import annotations
import datetime
import platform
import socket
import subprocess
import psutil
from rich.console import Console
from rich.table import Table
from rich import box

from modules.utils import human_size, section_header


def _uptime_str() -> str:
    boot = psutil.boot_time()
    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot)
    d, rem = divmod(int(delta.total_seconds()), 86400)
    h, rem = divmod(rem, 3600)
    m      = rem // 60
    parts  = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    parts.append(f"{m}m")
    return " ".join(parts)


def _cpu_name() -> str:
    try:
        r = subprocess.run(
            ["wmic", "cpu", "get", "Name", "/value"],
            capture_output=True, text=True, timeout=5,
        )
        for line in r.stdout.splitlines():
            if line.startswith("Name="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown"


def _os_build() -> str:
    try:
        r = subprocess.run(
            ["wmic", "os", "get", "Version,Caption,BuildNumber", "/value"],
            capture_output=True, text=True, timeout=5,
        )
        fields: dict[str, str] = {}
        for line in r.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                fields[k.strip()] = v.strip()
        caption = fields.get("Caption", platform.version())
        build   = fields.get("BuildNumber", "")
        return f"{caption}  (Build {build})" if build else caption
    except Exception:
        return platform.version()


def _bar(pct: float, width: int = 18) -> str:
    filled = int(pct / 100 * width)
    color  = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/] {pct:.1f}%"


def _disk_rows() -> list[tuple]:
    rows = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        bar = _bar(usage.percent)
        rows.append((
            part.device,
            part.fstype,
            human_size(usage.total),
            human_size(usage.used),
            human_size(usage.free),
            bar,
        ))
    return rows


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    vm   = psutil.virtual_memory()
    freq = psutil.cpu_freq()
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(part.mountpoint)
            disks.append({"device": part.device, "fstype": part.fstype,
                          "total_bytes": u.total, "used_bytes": u.used,
                          "free_bytes": u.free, "percent": u.percent})
        except PermissionError:
            pass

    bat = psutil.sensors_battery()
    return {
        "os":       _os_build(),
        "hostname": socket.gethostname(),
        "uptime":   _uptime_str(),
        "cpu": {
            "name":        _cpu_name(),
            "cores_phys":  psutil.cpu_count(logical=False),
            "cores_logic": psutil.cpu_count(logical=True),
            "freq_mhz":    round(freq.current) if freq else None,
            "usage_pct":   psutil.cpu_percent(interval=1),
        },
        "ram": {
            "total_bytes": vm.total,
            "used_bytes":  vm.used,
            "free_bytes":  vm.available,
            "percent":     vm.percent,
        },
        "disks": disks,
        "battery": {
            "percent":   bat.percent if bat else None,
            "plugged_in": bat.power_plugged if bat else None,
        } if bat else None,
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "SYSTEM INFORMATION")

    vm   = psutil.virtual_memory()
    freq = psutil.cpu_freq()

    # ── Overview table ────────────────────────────────────────────────────────
    ov = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    ov.add_column("Key",   style="dim",   width=14)
    ov.add_column("Value", width=56)

    ov.add_row("OS",       _os_build())
    ov.add_row("Hostname", socket.gethostname())
    ov.add_row("Uptime",   _uptime_str())
    ov.add_row("",         "")

    cpu_name  = _cpu_name()
    cpu_cores = f"{psutil.cpu_count(logical=False)}C / {psutil.cpu_count(logical=True)}T"
    cpu_freq  = f"@ {freq.current/1000:.2f} GHz" if freq else ""
    cpu_usage = psutil.cpu_percent(interval=0.5)
    ov.add_row("CPU",  f"[bold]{cpu_name}[/]  {cpu_cores}  {cpu_freq}")
    ov.add_row("",     f"  Usage  {_bar(cpu_usage)}")
    ov.add_row("",     "")

    ov.add_row("RAM",
               f"[bold]{human_size(vm.total)}[/]  used {human_size(vm.used)}  "
               f"free [bold green]{human_size(vm.available)}[/]")
    ov.add_row("",     f"  Usage  {_bar(vm.percent)}")

    bat = psutil.sensors_battery()
    if bat:
        plug = "[green]Plugged in[/]" if bat.power_plugged else "[yellow]On battery[/]"
        ov.add_row("Battery", f"{bat.percent:.0f}%  {plug}")

    console.print(ov)

    # ── Disk table ────────────────────────────────────────────────────────────
    disk_rows = _disk_rows()
    if disk_rows:
        console.print("  [bold cyan]Disks[/]\n")
        dtbl = Table(box=box.SIMPLE, header_style="bold cyan", padding=(0, 1))
        dtbl.add_column("Drive",  width=8)
        dtbl.add_column("FS",     width=6)
        dtbl.add_column("Total",  justify="right", width=10)
        dtbl.add_column("Used",   justify="right", width=10)
        dtbl.add_column("Free",   justify="right", width=10)
        dtbl.add_column("Usage",  width=26)
        for row in disk_rows:
            dtbl.add_row(*row)
        console.print(dtbl)

    console.print()
