"""
Tech Bytes Design — SysCleaner  v1.0.0
Windows system utility: cache cleaner · network refresh · RAM optimizer
system info · event log viewer · threat scanner · smart tips

Usage (interactive):  python main.py
Usage (agent / CLI):  python main.py [command ...] [-y] [-j]

Commands: clean  network  ram  info  logs  threats  tips  all
Flags:    -y / --yes    auto-confirm prompts (for scripted / AI use)
          -j / --json   output structured JSON then exit
"""
from __future__ import annotations
import argparse
import ctypes
import json
import sys

import psutil
from modules.logger import install_exception_hook, log_info, log_error, setup as _setup_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.prompt import Prompt
from rich.text import Text
from rich.rule import Rule
from rich import box

APP_NAME    = "SysCleaner"
APP_VERSION = "1.0.0"
COMPANY     = "Tech Bytes Design"
WEBSITE     = "techbytesdesign.in"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _pct_color(pct: float, warn: float = 70, crit: float = 85) -> str:
    if pct >= crit:  return "red"
    if pct >= warn:  return "yellow"
    return "green"


def _quick_stats() -> str:
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        vm  = psutil.virtual_memory()
        cc  = _pct_color(cpu, 50, 85)
        rc  = _pct_color(vm.percent)
        disk_part = ""
        try:
            u  = psutil.disk_usage("C:\\")
            dc = _pct_color(u.percent)
            disk_part = f"  [dim]│[/]  C:\\ [{dc}]{u.percent:.0f}%[/]"
        except Exception:
            pass
        return f"CPU [{cc}]{cpu:.0f}%[/]  RAM [{rc}]{vm.percent:.0f}%[/]{disk_part}"
    except Exception:
        return ""


# ── Header ────────────────────────────────────────────────────────────────────

def _show_header(console: Console, is_admin: bool) -> None:
    admin_txt = "[bold green]● ADMIN[/]" if is_admin else "[bold yellow]● USER[/]"
    stats     = _quick_stats()

    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)
    grid.add_column(justify="right")

    grid.add_row(
        Text.from_markup(f"[bold cyan]{APP_NAME}[/]  [dim]Windows System Utility[/]"),
        Text.from_markup(f"[dim]{COMPANY}[/]  [bold]v{APP_VERSION}[/]"),
    )
    grid.add_row(
        Text.from_markup(f"{admin_txt}  [dim]│[/]  {stats}"),
        Text.from_markup(f"[dim]{WEBSITE}[/]"),
    )

    console.print(Panel(grid, box=box.DOUBLE_EDGE, border_style="cyan", padding=(0, 2)))
    console.print()


# ── Menu ──────────────────────────────────────────────────────────────────────

_MENU_GROUPS = [
    ("MAINTENANCE", [
        ("1", "clean",   "Clean Caches & Temp Files",  "Browser · dev tools · Windows temp"),
        ("2", "network", "Refresh Network",             "DNS flush · Winsock reset · adapters"),
        ("3", "ram",     "Optimize RAM",                "Live stats · standby memory purge"),
    ]),
    ("DIAGNOSTICS", [
        ("4", "info",    "System Information",          "CPU · RAM · disk · OS · uptime"),
        ("5", "logs",    "View Error Logs",             "Last 10 critical/error/warning events"),
        ("6", "threats", "Threat Scan",                 "Processes · startup · hosts · ports"),
        ("7", "tips",    "Tips & Recommendations",      "Smart advice based on your system"),
    ]),
    ("", [
        ("8", "all",  "★  Full System Report", "Run all modules in sequence"),
        ("0", "exit", "✕  Exit",               ""),
    ]),
]


def _show_menu(console: Console) -> None:
    tbl = Table(box=box.ROUNDED, border_style="dim cyan",
                show_header=False, padding=(0, 2), expand=False)
    tbl.add_column("Key",   style="bold cyan", width=4)
    tbl.add_column("Name",  style="bold",      width=30)
    tbl.add_column("Desc",  style="dim",       width=40)

    for group_name, items in _MENU_GROUPS:
        if group_name:
            tbl.add_row("", f"[dim]{group_name}[/]", "", style="dim")
        for key, _, name, desc in items:
            if key == "0":
                tbl.add_row(f"[red]{key}[/]", f"[red]{name}[/]", desc)
            elif key == "8":
                tbl.add_row(f"[bold yellow]{key}[/]", f"[bold yellow]{name}[/]", desc)
            else:
                tbl.add_row(key, name, desc)

    console.print(tbl)
    console.print()


def _all_keys() -> list[str]:
    return [item[0] for group in _MENU_GROUPS for item in group[1]]


def _key_to_cmd() -> dict[str, str]:
    return {item[0]: item[1] for group in _MENU_GROUPS for item in group[1]}


# ── Module runner ─────────────────────────────────────────────────────────────

def _import_mods():
    from modules import cleaner, network, memory, sysinfo, logs, threats, tips
    return cleaner, network, memory, sysinfo, logs, threats, tips


def _run_cmd(
    cmd: str,
    console: Console,
    is_admin: bool,
    auto_confirm: bool,
    mods,
) -> None:
    cl, net, mem, si, lg, thr, tip = mods

    ORDER = ["info", "clean", "network", "ram", "logs", "threats", "tips"]

    dispatch = {
        "clean":   lambda: cl.run(console,  is_admin, auto_confirm),
        "network": lambda: net.run(console, is_admin, auto_confirm),
        "ram":     lambda: mem.run(console, is_admin, auto_confirm),
        "info":    lambda: si.run(console,  is_admin, auto_confirm),
        "logs":    lambda: lg.run(console,  is_admin, auto_confirm),
        "threats": lambda: thr.run(console, is_admin, auto_confirm),
        "tips":    lambda: tip.run(console, is_admin, auto_confirm),
    }

    if cmd == "all":
        for key in ORDER:
            console.print(Rule(style="dim cyan"))
            dispatch[key]()
    elif cmd in dispatch:
        dispatch[cmd]()


# ── Interactive mode ──────────────────────────────────────────────────────────

def _interactive(console: Console, is_admin: bool) -> None:
    mods    = _import_mods()
    k2c     = _key_to_cmd()
    choices = _all_keys()

    while True:
        console.clear()
        _show_header(console, is_admin)
        _show_menu(console)

        choice = Prompt.ask(
            "  [bold cyan]Select[/]",
            choices=choices,
            default="0",
            show_choices=False,
        )

        if choice == "0":
            console.print(
                f"\n  [bold cyan]Stay clean. Stay fast. — {COMPANY}[/]\n"
            )
            break

        cmd = k2c[choice]
        console.clear()
        _show_header(console, is_admin)

        try:
            _run_cmd(cmd, console, is_admin, auto_confirm=False, mods=mods)
        except Exception as exc:
            console.print(f"  [red]Error:[/] {exc}")

        Prompt.ask("\n  [dim]Press Enter to return to menu[/]", default="")


# ── Agent / CLI mode ──────────────────────────────────────────────────────────

def _agent(commands: list[str], is_admin: bool, json_mode: bool, auto_confirm: bool) -> None:
    console = Console(highlight=False)
    mods    = _import_mods()
    cl, net, mem, si, lg, thr, tip = mods

    if json_mode:
        cmd_map = {
            "clean":   lambda: cl.report(is_admin),
            "network": lambda: net.report(is_admin),
            "ram":     lambda: mem.report(is_admin),
            "info":    lambda: si.report(is_admin),
            "logs":    lambda: lg.report(is_admin),
            "threats": lambda: thr.report(is_admin),
            "tips":    lambda: tip.report(is_admin),
        }
        if "all" in commands:
            commands = list(cmd_map.keys())
        result: dict = {}
        for cmd in commands:
            if cmd in cmd_map:
                try:
                    result[cmd] = cmd_map[cmd]()
                except Exception as exc:
                    result[cmd] = {"error": str(exc)}
        print(json.dumps(result, indent=2, default=str))
        return

    _show_header(console, is_admin)
    if "all" in commands:
        commands = ["info", "clean", "network", "ram", "logs", "threats", "tips"]
    for cmd in commands:
        try:
            _run_cmd(cmd, console, is_admin, auto_confirm, mods)
        except Exception as exc:
            console.print(f"  [red]Error running '{cmd}':[/] {exc}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="syscleaner",
        description=f"{COMPANY} — {APP_NAME}  |  Windows System Utility  v{APP_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                    # interactive menu\n"
            "  python main.py info               # system info only\n"
            "  python main.py clean -y           # clean without prompt\n"
            "  python main.py all -y -j          # full report as JSON\n"
            "  python main.py threats logs       # threat scan + error logs\n"
        ),
    )
    parser.add_argument(
        "commands", nargs="*",
        choices=["clean", "network", "ram", "info", "logs", "threats", "tips", "all"],
        metavar="command",
        help="One or more: clean  network  ram  info  logs  threats  tips  all",
    )
    parser.add_argument("-y", "--yes",  action="store_true", help="Auto-confirm all prompts")
    parser.add_argument("-j", "--json", action="store_true", help="Output structured JSON")

    args     = parser.parse_args()
    is_admin = _is_admin()

    # Initialise logger and install crash hook on every run
    _setup_logger()
    install_exception_hook()
    log_info(f"Session start  admin={is_admin}  args={args.commands}", module="main")

    try:
        if args.commands:
            _agent(args.commands, is_admin, args.json, args.yes)
        else:
            _interactive(Console(), is_admin)
    except Exception as exc:
        log_error(str(exc), module="main", exc=exc)
        raise


if __name__ == "__main__":
    main()
