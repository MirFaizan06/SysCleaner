"""Startup Manager — view and toggle startup programs."""
from __future__ import annotations
import os
import winreg
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import box

from modules.utils import section_header, status_icon


STARTUP_KEYS = [
    (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",           "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",           "HKLM"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM32"),
]

STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup",
)


@dataclass
class StartupEntry:
    idx: int
    hive: str
    key_path: str
    raw_name: str          # name exactly as stored in registry
    display_name: str      # without "DISABLED_" prefix
    command: str
    enabled: bool
    hive_const: int | None = field(default=None, repr=False)


def _load_entries() -> list[StartupEntry]:
    entries: list[StartupEntry] = []
    idx = 0

    for hive_const, key_path, hive_name in STARTUP_KEYS:
        try:
            key = winreg.OpenKey(hive_const, key_path)
        except OSError:
            continue
        i = 0
        while True:
            try:
                raw_name, value, _ = winreg.EnumValue(key, i)
            except OSError:
                break
            enabled = not raw_name.upper().startswith("DISABLED_")
            display = raw_name[len("DISABLED_"):] if not enabled else raw_name
            entries.append(StartupEntry(
                idx=idx, hive=hive_name, key_path=key_path,
                raw_name=raw_name, display_name=display,
                command=value[:120], enabled=enabled,
                hive_const=hive_const,
            ))
            idx += 1
            i += 1
        winreg.CloseKey(key)

    if os.path.isdir(STARTUP_FOLDER):
        for f in os.listdir(STARTUP_FOLDER):
            entries.append(StartupEntry(
                idx=idx, hive="Folder", key_path=STARTUP_FOLDER,
                raw_name=f, display_name=f,
                command="(startup folder shortcut)",
                enabled=True, hive_const=None,
            ))
            idx += 1

    return entries


def _toggle(entry: StartupEntry) -> tuple[bool, str]:
    """Toggle entry. Returns (success, message)."""
    if entry.hive_const is None:
        return False, "Folder shortcuts must be managed via File Explorer or Task Manager."

    access = winreg.KEY_READ | winreg.KEY_WRITE
    try:
        key = winreg.OpenKey(entry.hive_const, entry.key_path, 0, access)
    except PermissionError:
        return False, "Permission denied — run as Administrator to modify HKLM entries."
    except OSError as exc:
        return False, str(exc)

    try:
        value, _ = winreg.QueryValueEx(key, entry.raw_name)
        if entry.enabled:
            new_name = f"DISABLED_{entry.display_name}"
            winreg.SetValueEx(key, new_name, 0, winreg.REG_SZ, value)
            winreg.DeleteValue(key, entry.raw_name)
            entry.raw_name = new_name
            entry.enabled  = False
            return True, f"Disabled  '{entry.display_name}'"
        else:
            winreg.SetValueEx(key, entry.display_name, 0, winreg.REG_SZ, value)
            winreg.DeleteValue(key, entry.raw_name)
            entry.raw_name = entry.display_name
            entry.enabled  = True
            return True, f"Enabled   '{entry.display_name}'"
    except Exception as exc:
        return False, str(exc)
    finally:
        winreg.CloseKey(key)


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    entries = _load_entries()
    return {
        "count":   len(entries),
        "enabled": sum(1 for e in entries if e.enabled),
        "entries": [
            {
                "idx":     e.idx,
                "hive":    e.hive,
                "name":    e.display_name,
                "command": e.command,
                "enabled": e.enabled,
            }
            for e in entries
        ],
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "STARTUP MANAGER", "view · enable · disable startup programs")

    entries = _load_entries()
    if not entries:
        console.print("  [dim]No startup entries found.[/]\n")
        return

    enabled_count  = sum(1 for e in entries if e.enabled)
    disabled_count = len(entries) - enabled_count
    console.print(
        f"  [bold]{len(entries)} entries[/]  "
        f"[green]{enabled_count} enabled[/]  [dim]{disabled_count} disabled[/]\n"
    )

    tbl = Table(box=box.SIMPLE, header_style="bold cyan", padding=(0, 1))
    tbl.add_column("#",       width=4,  justify="right", style="dim")
    tbl.add_column("Status",  width=9)
    tbl.add_column("Source",  width=8,  style="dim")
    tbl.add_column("Name",    width=30)
    tbl.add_column("Command", width=50, style="dim")

    for e in entries:
        status     = "[bold green]  ON[/]" if e.enabled else "[dim]  OFF[/]"
        name_style = "bold white" if e.enabled else "dim"
        tbl.add_row(
            str(e.idx), status, e.hive,
            f"[{name_style}]{e.display_name[:30]}[/]",
            e.command[:50],
        )
    console.print(tbl)

    if auto_confirm:
        console.print()
        return

    console.print(
        "  [dim]Enter a number to toggle ON/OFF, or press Enter to finish.[/]\n"
        "  [dim]Disabling does NOT delete — it can be re-enabled anytime.[/]\n"
    )
    if not is_admin:
        console.print(
            "  [yellow]⚠[/]  [dim]HKLM entries require Administrator. "
            "HKCU entries can be toggled now.[/]\n"
        )

    while not auto_confirm:
        choice = Prompt.ask("  [bold cyan]Toggle #[/]", default="")
        if not choice:
            break

        try:
            idx = int(choice.strip())
        except ValueError:
            console.print("  [dim]Enter a number or press Enter to skip.[/]")
            continue

        entry = next((e for e in entries if e.idx == idx), None)
        if entry is None:
            console.print(f"  [red]No entry #{idx}[/]")
            continue

        ok, msg = _toggle(entry)
        icon = "[bold green]✔[/]" if ok else "[bold red]✘[/]"
        console.print(f"  {icon}  {msg}\n")

    console.print()
