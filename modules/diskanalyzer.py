"""Disk Analyzer — top-level folder sizes with usage visualization."""
from __future__ import annotations
import concurrent.futures
import os
import threading
import psutil
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from modules.utils import human_size, section_header


SKIP_DIRS = frozenset({
    'windows', 'system volume information', '$recycle.bin',
    'recovery', 'boot', 'perflogs', '$windows.~ws', 'msocache',
    '$windows.~bt', 'config.msi', 'intel', 'amd',
})

# Well-known dirs scanned first (fast, targeted)
_USER_DIRS = [
    ("Downloads",           os.path.expanduser("~/Downloads")),
    ("Documents",           os.path.expanduser("~/Documents")),
    ("Videos",              os.path.expanduser("~/Videos")),
    ("Pictures",            os.path.expanduser("~/Pictures")),
    ("Desktop",             os.path.expanduser("~/Desktop")),
    ("AppData\\Local",      os.path.expandvars("%LOCALAPPDATA%")),
    ("AppData\\Roaming",    os.path.expandvars("%APPDATA%")),
    ("Program Files",       r"C:\Program Files"),
    ("Program Files (x86)", r"C:\Program Files (x86)"),
    ("Users (all)",         r"C:\Users"),
]


def _dir_size(path: str, max_depth: int = 3) -> int:
    """Return total bytes under path up to max_depth. Thread-safe."""
    total = 0
    try:
        for root, dirs, files in os.walk(path, onerror=None):
            depth = root.count(os.sep) - path.count(os.sep)
            if depth >= max_depth:
                dirs.clear()
            else:
                dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except (PermissionError, OSError):
        pass
    return total


def _size_with_timeout(path: str, timeout: float = 6.0) -> int:
    result: list[int] = [0]
    done = threading.Event()

    def _run() -> None:
        result[0] = _dir_size(path)
        done.set()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    done.wait(timeout)
    return result[0]


def _bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    color = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/] {pct:.1f}%"


def _scan_dirs(console: Console) -> list[tuple[str, int]]:
    """Scan known dirs in parallel with a spinner."""
    paths = [(label, path) for label, path in _USER_DIRS if os.path.isdir(path)]
    results: list[tuple[str, int]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[dim]Scanning {task.description}…[/]"),
        console=console,
        transient=True,
    ) as prog:
        task = prog.add_task("", total=len(paths))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            future_map = {pool.submit(_size_with_timeout, path, 6.0): label
                         for label, path in paths}
            for future in concurrent.futures.as_completed(future_map):
                label = future_map[future]
                try:
                    size = future.result()
                except Exception:
                    size = 0
                results.append((label, size))
                prog.advance(task)

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    drives = []
    for part in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(part.mountpoint)
            drives.append({
                "device": part.device,
                "fstype": part.fstype,
                "total_bytes": u.total,
                "used_bytes":  u.used,
                "free_bytes":  u.free,
                "percent":     u.percent,
            })
        except PermissionError:
            pass

    dirs = []
    for label, path in _USER_DIRS:
        if os.path.isdir(path):
            size = _size_with_timeout(path, 6.0)
            dirs.append({"label": label, "path": path, "bytes": size})
    dirs.sort(key=lambda x: x["bytes"], reverse=True)

    return {"drives": drives, "top_dirs": dirs}


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "DISK ANALYZER", "drive usage · top folders by size")

    # ── Drive summary ─────────────────────────────────────────────────────────
    console.print("  [bold]Drive Usage[/]\n")
    dtbl = Table(box=box.SIMPLE, header_style="bold cyan", padding=(0, 1))
    dtbl.add_column("Drive",  width=8)
    dtbl.add_column("FS",     width=6)
    dtbl.add_column("Total",  justify="right", width=10)
    dtbl.add_column("Used",   justify="right", width=10)
    dtbl.add_column("Free",   justify="right", width=10)
    dtbl.add_column("Usage",  width=28)

    for part in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        dtbl.add_row(
            part.device, part.fstype,
            human_size(u.total), human_size(u.used), human_size(u.free),
            _bar(u.percent),
        )
    console.print(dtbl)

    # ── Folder scan ───────────────────────────────────────────────────────────
    console.print("  [bold]Top Folders by Size[/]  [dim](scanning common locations…)[/]\n")
    dir_results = _scan_dirs(console)

    if not dir_results:
        console.print("  [dim]No folders found.[/]")
        console.print()
        return

    max_size = dir_results[0][1] if dir_results else 1

    ftbl = Table(box=box.SIMPLE, header_style="bold cyan", padding=(0, 1))
    ftbl.add_column("#",     width=3,  justify="right", style="dim")
    ftbl.add_column("Folder",  width=24)
    ftbl.add_column("Size",  width=10, justify="right")
    ftbl.add_column("Bar",   width=34)

    for i, (label, size) in enumerate(dir_results, 1):
        pct = (size / max_size * 100) if max_size > 0 else 0
        filled = int(pct / 100 * 28)
        bar = f"[cyan]{'█' * filled}{'░' * (28 - filled)}[/]"
        ftbl.add_row(str(i), label, human_size(size), bar)

    console.print(ftbl)

    # ── Tip ───────────────────────────────────────────────────────────────────
    console.print(
        "  [dim]Tip: use Clean (option 1) to free temp/browser/dev cache."
        "  AppData\\Local is often the largest space hog.[/]"
    )
    console.print()
