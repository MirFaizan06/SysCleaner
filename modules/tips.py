"""Smart system tips based on live system state."""
from __future__ import annotations
import datetime
import os
import psutil
from rich.console import Console
from rich.panel import Panel
from rich import box

from modules.utils import section_header


def _disk_tips() -> list[tuple[str, str]]:
    tips = []
    for part in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(part.mountpoint)
            pct = u.percent
            free_gb = u.free / 1_073_741_824
            if pct >= 95:
                tips.append(("critical",
                    f"{part.device} is [bold red]{pct:.0f}% full[/] ({free_gb:.1f} GB left). "
                    "Free space immediately — Windows needs ≥ 10% for updates and temp files."))
            elif pct >= 85:
                tips.append(("warning",
                    f"{part.device} is [yellow]{pct:.0f}% full[/] ({free_gb:.1f} GB left). "
                    "Run the Cleaner and consider moving large files to external storage."))
        except PermissionError:
            pass
    return tips


def _ram_tips() -> list[tuple[str, str]]:
    vm  = psutil.virtual_memory()
    tips = []
    if vm.percent >= 90:
        tips.append(("critical",
            f"RAM usage is [bold red]{vm.percent:.0f}%[/]. "
            "Close unused applications or run RAM optimization with Administrator rights."))
    elif vm.percent >= 75:
        tips.append(("warning",
            f"RAM usage is [yellow]{vm.percent:.0f}%[/]. "
            "Consider closing background apps or adding more RAM if this is frequent."))
    return tips


def _uptime_tips() -> list[tuple[str, str]]:
    boot   = psutil.boot_time()
    uptime = (datetime.datetime.now() - datetime.datetime.fromtimestamp(boot)).total_seconds()
    days   = uptime / 86400
    tips   = []
    if days >= 14:
        tips.append(("warning",
            f"System has been running for [yellow]{days:.0f} days[/] without a reboot. "
            "Rebooting clears memory, applies pending updates, and refreshes Windows services."))
    elif days >= 7:
        tips.append(("info",
            f"Uptime is {days:.0f} days. A weekly reboot is a healthy habit."))
    return tips


def _temp_tips() -> list[tuple[str, str]]:
    tips    = []
    temp    = os.environ.get("TEMP", "")
    tempdir = os.environ.get("LOCALAPPDATA", "")

    for path, label in [(temp, "User Temp"), (tempdir + r"\Temp", "Local App Temp")]:
        if not os.path.isdir(path):
            continue
        try:
            total = sum(
                os.path.getsize(os.path.join(root, f))
                for root, _, files in os.walk(path, onerror=None)
                for f in files
                if not os.path.getsize.__doc__  or True
            )
            gb = total / 1_073_741_824
            if gb >= 2:
                tips.append(("info",
                    f"[bold]{label}[/] contains {gb:.1f} GB. Run the Cleaner to reclaim this space."))
        except OSError:
            pass
    return tips


def _cpu_tips() -> list[tuple[str, str]]:
    usage = psutil.cpu_percent(interval=0.5)
    tips  = []
    if usage >= 85:
        tips.append(("warning",
            f"CPU is at [yellow]{usage:.0f}%[/] right now. "
            "Check Task Manager for runaway processes."))
    return tips


def _battery_tips() -> list[tuple[str, str]]:
    bat  = psutil.sensors_battery()
    tips = []
    if bat and not bat.power_plugged and bat.percent < 20:
        tips.append(("critical",
            f"Battery is at [red]{bat.percent:.0f}%[/] and not charging. Plug in soon."))
    return tips


def _general_tips() -> list[tuple[str, str]]:
    return [
        ("info", "Keep [bold]Windows Defender[/] real-time protection enabled at all times."),
        ("info", "Enable [bold]BitLocker[/] on your system drive to protect data if the device is lost."),
        ("info", "Regularly back up important files to an external drive or cloud storage."),
        ("info", "Disable startup programs you don't need: [dim]Task Manager → Startup Apps[/]."),
        ("info", "Prefer wired Ethernet over Wi-Fi for stability when gaming or doing large uploads."),
    ]


ICONS = {
    "critical": "[bold red]  ▲[/]",
    "warning":  "[yellow]  ●[/]",
    "info":     "[cyan]  ›[/]",
}


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    all_tips = (
        _disk_tips() + _ram_tips() + _uptime_tips() +
        _temp_tips() + _cpu_tips() + _battery_tips()
    )
    return {
        "tips": [{"level": level, "message": msg} for level, msg in all_tips],
        "general": [msg for _, msg in _general_tips()],
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "TIPS & RECOMMENDATIONS")

    all_tips = (
        _disk_tips() + _ram_tips() + _uptime_tips() +
        _temp_tips() + _cpu_tips() + _battery_tips()
    )

    if not all_tips:
        console.print("  [bold green]✔  Your system looks healthy![/]  No urgent recommendations.\n")
    else:
        for level, msg in all_tips:
            console.print(f"{ICONS[level]}  {msg}")
        console.print()

    console.print("  [bold cyan]General best practices[/]")
    for _, msg in _general_tips():
        console.print(f"{ICONS['info']}  {msg}")

    console.print()
