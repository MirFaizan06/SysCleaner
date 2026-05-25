"""
Tech Bytes Design — SysCleaner  v1.1.0
Windows system utility: cache cleaner · network refresh · RAM optimizer
disk analyzer · startup manager · HTML report · event log viewer · threat scanner

Usage (interactive):  sysc   (or: python main.py)
Usage (agent / CLI):  sysc [command ...] [-y] [-j]

Commands: clean  network  ram  info  disk  startup  logs  threats  tips  report  all
Flags:    -y / --yes    auto-confirm prompts (for scripted / AI use)
          -j / --json   output structured JSON then exit
"""
from __future__ import annotations
import argparse
import ctypes
import datetime
import json
import os
import pathlib
import sys

import psutil
from modules.logger import install_exception_hook, log_info, log_error, setup as _setup_logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.prompt import Prompt
from rich import box

# Force UTF-8 so Unicode box-drawing / star chars work on any Windows terminal
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

APP_NAME    = "SysCleaner"
APP_VERSION = "1.1.0"
COMPANY     = "Tech Bytes Design"
WEBSITE     = "techbytesdesign.in"

# Modules that produce exportable diagnostic data
_EXPORTABLE = {"info", "logs", "threats", "disk", "startup"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _try_elevate() -> bool:
    """
    Re-launch the current process with UAC elevation.
    Returns True if the elevated process was launched (caller should sys.exit).
    """
    if getattr(sys, "frozen", False):
        exe    = sys.executable
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
    else:
        script = os.path.abspath(sys.argv[0])
        exe    = sys.executable
        params = f'"{script}"'
        extra  = " ".join(f'"{a}"' for a in sys.argv[1:])
        if extra:
            params += " " + extra

    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    return rc > 32


def _cls() -> None:
    os.system("cls")


def _pct_color(pct: float, warn: float = 70, crit: float = 85) -> str:
    if pct >= crit: return "red"
    if pct >= warn: return "yellow"
    return "green"


def _quick_stats() -> str:
    try:
        cpu = psutil.cpu_percent(interval=0.25)
        vm  = psutil.virtual_memory()
        cc  = _pct_color(cpu, 50, 85)
        rc  = _pct_color(vm.percent)
        parts = [
            f"CPU [{cc}]{cpu:.0f}%[/]",
            f"RAM [{rc}]{vm.percent:.0f}%[/]",
        ]
        try:
            u  = psutil.disk_usage("C:\\")
            dc = _pct_color(u.percent)
            parts.append(f"C:\\ [{dc}]{u.percent:.0f}%[/]")
        except Exception:
            pass
        return "  ·  ".join(parts)
    except Exception:
        return ""


def _export_dir() -> pathlib.Path:
    d = pathlib.Path.home() / "Documents" / "SysCleaner" / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _dict_to_txt(data: dict, indent: int = 0) -> list[str]:
    lines: list[str] = []
    pad = "  " * indent
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{pad}{k}:")
            lines.extend(_dict_to_txt(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{pad}{k}:")
            for item in v:
                if isinstance(item, dict):
                    lines.extend(_dict_to_txt(item, indent + 1))
                    lines.append("")
                else:
                    lines.append(f"{pad}  - {item}")
        else:
            lines.append(f"{pad}{k}: {v}")
    return lines


def _offer_export(console: Console, cmd: str, get_data) -> None:
    """Prompt user to export diagnostic results as JSON or TXT."""
    console.print()
    console.print(
        "  [dim]Export lets you save these results for auditing, sharing, or AI analysis.[/]"
    )
    choice = Prompt.ask(
        "  [bold cyan]Save results?[/]  [dim][j=JSON  t=TXT  Enter=skip][/]",
        choices=["j", "t", ""],
        default="",
        show_choices=False,
    )
    if not choice:
        return

    try:
        data = get_data()
        ts   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        d    = _export_dir()

        if choice == "j":
            path = d / f"syscleaner_{cmd}_{ts}.json"
            path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        else:
            path = d / f"syscleaner_{cmd}_{ts}.txt"
            lines = [
                f"SysCleaner {APP_VERSION} — {cmd.upper()} export",
                f"Generated: {datetime.datetime.now().isoformat()}",
                "=" * 60,
                "",
            ] + _dict_to_txt(data)
            path.write_text("\n".join(lines), encoding="utf-8")

        console.print(f"\n  [bold green]✔[/]  Saved: [dim]{path}[/]")
    except Exception as exc:
        console.print(f"\n  [red]Export failed:[/] {exc}")


# ── Header ────────────────────────────────────────────────────────────────────

def _show_header(console: Console, is_admin: bool) -> None:
    stats    = _quick_stats()
    mode_tag = "[bold green]● ADMIN[/]" if is_admin else "[bold yellow]● USER[/]"

    grid = Table.grid(padding=(0, 1), expand=True)
    grid.add_column(ratio=1)
    grid.add_column(justify="right")

    grid.add_row(
        Text.from_markup(f"[bold cyan]{APP_NAME}[/]  [dim]Windows System Utility[/]"),
        Text.from_markup(f"[dim]{COMPANY}[/]  [dim]v{APP_VERSION}[/]"),
    )
    grid.add_row(
        Text.from_markup(f"{mode_tag}  [dim]{stats}[/]"),
        Text.from_markup(f"[dim]{WEBSITE}[/]"),
    )

    console.print(Panel(grid, border_style="cyan", box=box.HEAVY, padding=(0, 2)))


# ── Menu ──────────────────────────────────────────────────────────────────────

_GROUPS = [
    ("MAINTENANCE", [
        ("1", "clean",   "Clean Caches & Temp Files",   "browser · dev tools · windows temp"),
        ("2", "network", "Refresh Network",              "DNS flush · winsock reset · adapters"),
        ("3", "ram",     "Optimize RAM",                 "live stats · standby memory purge"),
    ]),
    ("DIAGNOSTICS", [
        ("4", "info",    "System Information",           "CPU · RAM · disk · OS · uptime"),
        ("5", "disk",    "Disk Analyzer",                "top folders by size · drive usage"),
        ("6", "startup", "Startup Manager",              "view · enable · disable startup entries"),
        ("7", "logs",    "View Error Logs",              "last 10 critical/error/warning events"),
        ("8", "threats", "Threat Scan",                  "processes · startup · hosts · ports"),
        ("9", "tips",    "Tips & Recommendations",       "smart advice based on your system"),
    ]),
]
_EXTRA = [
    ("r", "report", "★  Generate HTML Report",   "full snapshot saved to Documents"),
    ("a", "all",    "★  Run All Modules",        "maintenance + diagnostics in sequence"),
    ("0", "exit",   "✕  Exit",                   ""),
]


def _show_menu(console: Console) -> None:
    console.print()
    for group_name, items in _GROUPS:
        console.print(f"  [bold dim]{group_name}[/]")
        console.print(f"  [dim]{'─' * 66}[/]")
        for key, _, name, desc in items:
            key_txt  = Text(f" {key} ", style="bold cyan on #0d1620")
            name_txt = Text(f"  {name:<32}", style="bold white")
            desc_txt = Text(f"  {desc}", style="dim")
            row      = Text.assemble(key_txt, name_txt, desc_txt)
            console.print(f"  {row}")
        console.print()

    console.print(f"  [dim]{'─' * 66}[/]")
    for key, _, name, desc in _EXTRA:
        if key in ("r", "a"):
            key_s  = f"[bold yellow] {key.upper()} [/]"
            name_s = f"[bold yellow]  {name:<32}[/]"
        else:
            key_s  = f"[bold red] {key} [/]"
            name_s = f"[bold red]  {name:<32}[/]"
        desc_s = f"[dim]  {desc}[/]" if desc else ""
        console.print(f"  {key_s}{name_s}{desc_s}")
    console.print()


def _all_keys() -> list[str]:
    keys = [i[0] for _, items in _GROUPS for i in items]
    keys += [i[0] for i in _EXTRA]
    return keys


def _key_to_cmd() -> dict[str, str]:
    m = {i[0]: i[1] for _, items in _GROUPS for i in items}
    m.update({i[0]: i[1] for i in _EXTRA})
    return m


# ── Module runner ─────────────────────────────────────────────────────────────

def _import_mods():
    from modules import cleaner, network, memory, sysinfo, logs, threats, tips
    from modules import diskanalyzer, startup, htmlreport
    return cleaner, network, memory, sysinfo, logs, threats, tips, diskanalyzer, startup, htmlreport


def _run_cmd(cmd: str, console: Console, is_admin: bool, auto_confirm: bool, mods) -> None:
    cl, net, mem, si, lg, thr, tip, da, su, hr = mods
    ORDER = ["info", "clean", "network", "ram", "disk", "startup", "logs", "threats", "tips"]
    dispatch = {
        "clean":   lambda: cl.run(console,  is_admin, auto_confirm),
        "network": lambda: net.run(console, is_admin, auto_confirm),
        "ram":     lambda: mem.run(console, is_admin, auto_confirm),
        "info":    lambda: si.run(console,  is_admin, auto_confirm),
        "disk":    lambda: da.run(console,  is_admin, auto_confirm),
        "startup": lambda: su.run(console,  is_admin, auto_confirm),
        "logs":    lambda: lg.run(console,  is_admin, auto_confirm),
        "threats": lambda: thr.run(console, is_admin, auto_confirm),
        "tips":    lambda: tip.run(console, is_admin, auto_confirm),
        "report":  lambda: hr.run(console,  is_admin, auto_confirm),
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
    cl, net, mem, si, lg, thr, tip, da, su, hr = mods
    k2c     = _key_to_cmd()
    choices = _all_keys()

    # Build report lambdas for export (lazy — only called if user asks)
    _reporters = {
        "info":    lambda: si.report(is_admin),
        "disk":    lambda: da.report(is_admin),
        "logs":    lambda: lg.report(is_admin),
        "threats": lambda: thr.report(is_admin),
        "startup": lambda: su.report(is_admin),
    }

    while True:
        _cls()
        _show_header(console, is_admin)
        _show_menu(console)

        choice = Prompt.ask(
            "  [bold cyan]Select[/]",
            choices=choices,
            default="0",
            show_choices=False,
        )

        if choice == "0":
            _cls()
            console.print(f"\n  [bold cyan]Stay clean. Stay fast.[/]  [dim]— {COMPANY}[/]\n")
            break

        cmd = k2c[choice]
        _cls()
        _show_header(console, is_admin)
        console.print()

        try:
            _run_cmd(cmd, console, is_admin, auto_confirm=False, mods=mods)
        except Exception as exc:
            console.print(f"\n  [red]Error:[/] {exc}")
            log_error(str(exc), module=cmd, exc=exc)

        # Offer export for diagnostic commands
        if cmd in _EXPORTABLE and cmd in _reporters:
            _offer_export(console, cmd, _reporters[cmd])

        Prompt.ask("\n  [dim]Press Enter to return to menu[/]", default="")


# ── Agent / CLI mode ──────────────────────────────────────────────────────────

def _agent(commands: list[str], is_admin: bool, json_mode: bool, auto_confirm: bool) -> None:
    console = Console(highlight=False)
    mods    = _import_mods()
    cl, net, mem, si, lg, thr, tip, da, su, hr = mods

    if json_mode:
        cmd_map = {
            "clean":   lambda: cl.report(is_admin),
            "network": lambda: net.report(is_admin),
            "ram":     lambda: mem.report(is_admin),
            "info":    lambda: si.report(is_admin),
            "disk":    lambda: da.report(is_admin),
            "startup": lambda: su.report(is_admin),
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
    if not is_admin:
        console.print(
            "  [yellow]⚠[/]  [dim]Running as standard user — some features need Administrator.[/]\n"
        )

    if "all" in commands:
        commands = ["info", "clean", "network", "ram", "disk", "startup", "logs", "threats", "tips"]
    for cmd in commands:
        console.print()
        try:
            _run_cmd(cmd, console, is_admin, auto_confirm, mods)
        except Exception as exc:
            console.print(f"  [red]Error running '{cmd}':[/] {exc}")
            log_error(str(exc), module=cmd, exc=exc)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sysc",
        description=f"{COMPANY} — {APP_NAME}  |  Windows System Utility  v{APP_VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  sysc                        # interactive menu\n"
            "  sysc info                   # system info only\n"
            "  sysc clean -y              # clean without prompt\n"
            "  sysc all -y -j            # full report as JSON\n"
            "  sysc threats logs          # threat scan + error logs\n"
            "  sysc disk                  # disk space analyzer\n"
            "  sysc startup               # startup manager\n"
            "  sysc report                # generate HTML report\n"
        ),
    )
    parser.add_argument(
        "commands", nargs="*",
        choices=["clean", "network", "ram", "info", "disk", "startup",
                 "logs", "threats", "tips", "report", "all"],
        metavar="command",
        help="One or more: clean  network  ram  info  disk  startup  logs  threats  tips  report  all",
    )
    parser.add_argument("-y", "--yes",  action="store_true", help="Auto-confirm all prompts")
    parser.add_argument("-j", "--json", action="store_true", help="Output structured JSON")

    args     = parser.parse_args()
    is_admin = _is_admin()

    _setup_logger()
    install_exception_hook()
    log_info(f"Session start  v{APP_VERSION}  admin={is_admin}  args={args.commands}", module="main")

    # ── Admin elevation (interactive mode only) ────────────────────────────────
    if not is_admin and not args.commands:
        console = Console()
        console.print()
        console.print(
            "  [yellow]⚠[/]  [bold]SysCleaner works best with Administrator rights.[/]\n"
            "     Full cleaning, Winsock reset, and RAM optimization require elevation.\n"
        )
        elevate = Prompt.ask(
            "  Run as Administrator?",
            choices=["y", "n"],
            default="y",
        )
        if elevate == "y":
            launched = _try_elevate()
            if launched:
                sys.exit(0)
            else:
                console.print(
                    "  [yellow]UAC was declined or failed.[/] Continuing as standard user.\n"
                )

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
