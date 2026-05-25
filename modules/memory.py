"""RAM diagnostics and standby memory optimization."""
from __future__ import annotations
import ctypes
import ctypes.wintypes
import psutil
from rich.console import Console
from rich.table import Table
from rich import box

from modules.utils import human_size, section_header


# ── Windows privilege helper ──────────────────────────────────────────────────

_TOKEN_ADJUST_PRIVILEGES = 0x0020
_TOKEN_QUERY             = 0x0008
_SE_PRIVILEGE_ENABLED    = 0x0002


def _enable_privilege(name: str) -> bool:
    try:
        h_token = ctypes.wintypes.HANDLE()
        ctypes.windll.advapi32.OpenProcessToken(
            ctypes.windll.kernel32.GetCurrentProcess(),
            _TOKEN_ADJUST_PRIVILEGES | _TOKEN_QUERY,
            ctypes.byref(h_token),
        )

        luid = ctypes.wintypes.LUID()
        ctypes.windll.advapi32.LookupPrivilegeValueW(None, name, ctypes.byref(luid))

        class _LuidAttr(ctypes.Structure):
            _fields_ = [("Luid", ctypes.wintypes.LUID), ("Attributes", ctypes.wintypes.DWORD)]

        class _TokenPriv(ctypes.Structure):
            _fields_ = [("Count", ctypes.wintypes.DWORD), ("Privs", _LuidAttr * 1)]

        tp = _TokenPriv()
        tp.Count = 1
        tp.Privs[0].Luid = luid
        tp.Privs[0].Attributes = _SE_PRIVILEGE_ENABLED

        ctypes.windll.advapi32.AdjustTokenPrivileges(
            h_token, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None
        )
        return ctypes.windll.kernel32.GetLastError() == 0
    except Exception:
        return False


def _purge_standby_list() -> bool:
    """Release standby (cached) pages back to the available pool."""
    try:
        _enable_privilege("SeProfileSingleProcessPrivilege")
        _SYSTEM_MEMORY_LIST_INFORMATION = 80
        _MemoryPurgeStandbyList = ctypes.c_int(4)
        status = ctypes.windll.ntdll.NtSetSystemInformation(
            _SYSTEM_MEMORY_LIST_INFORMATION,
            ctypes.byref(_MemoryPurgeStandbyList),
            ctypes.sizeof(_MemoryPurgeStandbyList),
        )
        return status == 0
    except Exception:
        return False


def _get_ram() -> dict:
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return {
        "total":     vm.total,
        "used":      vm.used,
        "free":      vm.available,
        "cached":    getattr(vm, "cached", 0),
        "pct":       vm.percent,
        "swap_total": sw.total,
        "swap_used":  sw.used,
        "swap_pct":   sw.percent,
    }


def _bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    color  = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
    bar    = "█" * filled + "░" * (width - filled)
    return f"[{color}]{bar}[/] {pct:.1f}%"


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    before = _get_ram()
    purged = False
    if is_admin:
        purged = _purge_standby_list()
    after = _get_ram()
    freed = max(0, before["used"] - after["used"])
    return {
        "before": before,
        "after":  after,
        "purged_standby": purged,
        "freed_bytes": freed,
        "freed_human": human_size(freed),
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "RAM DIAGNOSTICS & OPTIMIZATION")

    before = _get_ram()

    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    tbl.add_column("Label", style="dim",  width=14)
    tbl.add_column("Value", width=36)

    tbl.add_row("Total RAM",  f"[bold]{human_size(before['total'])}[/]")
    tbl.add_row("In Use",     f"[bold]{human_size(before['used'])}[/]  {_bar(before['pct'])}")
    tbl.add_row("Available",  f"[bold green]{human_size(before['free'])}[/]")
    if before["swap_total"]:
        tbl.add_row("Swap",   f"{human_size(before['swap_used'])} / {human_size(before['swap_total'])}  {_bar(before['swap_pct'])}")
    console.print(tbl)
    console.print()

    if is_admin:
        console.print("  Purging standby memory list…", end="")
        ok = _purge_standby_list()
        if ok:
            after  = _get_ram()
            freed  = max(0, before["used"] - after["used"])
            console.print(f"  [green]done.[/]  Freed ≈ [bold green]{human_size(freed)}[/]")
        else:
            console.print("  [yellow]No additional memory freed (standby list already empty).[/]")
    else:
        console.print(
            "  [dim]Run as Administrator to purge standby memory "
            "(can free several hundred MB on busy systems).[/]"
        )

    console.print()
