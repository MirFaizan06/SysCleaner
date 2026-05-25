"""
Cache and temp file cleaner.

SAFETY DESIGN:
- Every target path is explicitly whitelisted here; no user-supplied paths are ever cleaned.
- Firefox: only profile/cache2, profile/thumbnails, profile/OfflineCache subdirs (NEVER the Profiles root).
- JetBrains: only product/<version>/caches and product/<version>/log subdirs (NEVER the JetBrains root).
- Windows system paths (Temp, Prefetch) are allowed explicitly; all user paths require depth >= 5.
- A safe-path validator double-checks before scan/clean; forbidden if depth < 4 or inside System32/SysWOW64/ProgramFiles.
- Only directory CONTENTS are deleted, never the directory itself.
"""
from __future__ import annotations
import os
import shutil
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Confirm
from rich import box

from modules.utils import human_size, section_header


# ── Target definition ─────────────────────────────────────────────────────────

@dataclass
class _Target:
    name: str
    path: str
    admin_only: bool = False
    category: str = "system"


# ── Safety guard ──────────────────────────────────────────────────────────────

_EXPLICIT_SYSTEM_PATHS = frozenset(
    os.path.normcase(p) for p in [
        r"C:\Windows\Temp",
        r"C:\Windows\Prefetch",
    ]
)

_FORBIDDEN_PREFIXES = (
    os.path.normcase(r"C:\Windows\System32"),
    os.path.normcase(r"C:\Windows\SysWOW64"),
    os.path.normcase(r"C:\Program Files"),
    os.path.normcase(r"C:\Program Files (x86)"),
)


def _is_safe_target(path: str) -> bool:
    """Refuse to clean system-critical or too-shallow paths."""
    if not path or len(path) < 5:
        return False
    try:
        norm = os.path.normcase(os.path.abspath(path))

        # Explicitly whitelisted Windows system cache paths
        if norm in _EXPLICIT_SYSTEM_PATHS:
            return True

        # Never touch forbidden system directories
        if any(norm.startswith(fp) for fp in _FORBIDDEN_PREFIXES):
            return False

        # User paths must be at least 4 levels deep (e.g. C:\Users\Name\AppData\Xyz)
        parts = [p for p in norm.replace("/", "\\").split("\\") if p]
        return len(parts) >= 4
    except Exception:
        return False


# ── Target builder ────────────────────────────────────────────────────────────

def _build_targets() -> list[_Target]:
    e           = os.environ.get
    appdata     = e("APPDATA",      "")
    localdata   = e("LOCALAPPDATA", "")
    temp        = e("TEMP",         "")
    userprofile = e("USERPROFILE",  "")

    targets: list[_Target] = []

    def add(name: str, path: str, admin: bool = False, cat: str = "system") -> None:
        if path and _is_safe_target(path):
            targets.append(_Target(name, path, admin, cat))

    # ── Windows system caches ─────────────────────────────────────────────────
    add("User Temp",             temp,                                                                 False, "system")
    add("Windows Temp",          r"C:\Windows\Temp",                                                   True,  "system")
    add("Local App Temp",        os.path.join(localdata, "Temp"),                                      False, "system")
    add("Prefetch Cache",        r"C:\Windows\Prefetch",                                               True,  "system")
    add("WER Report Queue",      os.path.join(localdata, "Microsoft", "Windows", "WER", "ReportQueue"), False, "system")
    # Thumbnail / icon caches — this folder contains ONLY thumbcache_*.db and iconcache_*.db files
    add("Thumbnail Cache",       os.path.join(localdata, "Microsoft", "Windows", "Explorer"),          False, "system")
    add("D3D Shader Cache",      os.path.join(localdata, "D3DSCache"),                                 False, "system")

    # ── Browser caches (cache only — never bookmarks, passwords, history) ─────
    add("Chrome Cache",          os.path.join(localdata, "Google",    "Chrome",       "User Data", "Default", "Cache"),        False, "browser")
    add("Chrome Code Cache",     os.path.join(localdata, "Google",    "Chrome",       "User Data", "Default", "Code Cache"),   False, "browser")
    add("Chrome GPU Cache",      os.path.join(localdata, "Google",    "Chrome",       "User Data", "Default", "GPUCache"),     False, "browser")
    add("Edge Cache",            os.path.join(localdata, "Microsoft", "Edge",         "User Data", "Default", "Cache"),        False, "browser")
    add("Edge Code Cache",       os.path.join(localdata, "Microsoft", "Edge",         "User Data", "Default", "Code Cache"),   False, "browser")
    add("Edge GPU Cache",        os.path.join(localdata, "Microsoft", "Edge",         "User Data", "Default", "GPUCache"),     False, "browser")
    add("Brave Cache",           os.path.join(localdata, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache"),  False, "browser")
    add("Opera Cache",           os.path.join(appdata,   "Opera Software", "Opera Stable", "Cache"),                          False, "browser")

    # Firefox — per-profile cache dirs ONLY (never the Profiles root or any profile root)
    firefox_profiles_root = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if os.path.isdir(firefox_profiles_root):
        for profile in os.listdir(firefox_profiles_root):
            profile_path = os.path.join(firefox_profiles_root, profile)
            if not os.path.isdir(profile_path):
                continue
            for cache_sub in ("cache2", "thumbnails", "OfflineCache"):
                cache_path = os.path.join(profile_path, cache_sub)
                if os.path.isdir(cache_path):
                    targets.append(_Target(f"Firefox {cache_sub}", cache_path, False, "browser"))

    # ── Dev tool caches ───────────────────────────────────────────────────────
    add("npm Cache",             os.path.join(appdata,   "npm-cache"),                                False, "dev")
    add("npm Cache (Local)",     os.path.join(localdata, "npm-cache"),                                False, "dev")
    add("Yarn Cache",            os.path.join(localdata, "Yarn",     "Cache"),                        False, "dev")
    add("pnpm Cache",            os.path.join(localdata, "pnpm-cache"),                               False, "dev")
    add("pip Cache",             os.path.join(localdata, "pip",      "Cache"),                        False, "dev")
    add("uv Cache",              os.path.join(localdata, "uv",       "cache"),                        False, "dev")
    add("VS Code Cache",         os.path.join(appdata,   "Code",     "Cache"),                        False, "dev")
    add("VS Code CachedData",    os.path.join(appdata,   "Code",     "CachedData"),                   False, "dev")
    add("VS Code CachedExt",     os.path.join(appdata,   "Code",     "CachedExtensions"),             False, "dev")
    add("VS Code Logs",          os.path.join(appdata,   "Code",     "logs"),                         False, "dev")
    add("Gradle Cache",          os.path.join(userprofile, ".gradle", "caches"),                      False, "dev")
    add("Docker Logs",           os.path.join(localdata, "Docker",   "log"),                          False, "dev")
    add("Composer Cache",        os.path.join(localdata, "Composer", "files"),                        False, "dev")
    add("Cargo Registry",        os.path.join(userprofile, ".cargo", "registry", "cache"),            False, "dev")
    add("Go Build Cache",        os.path.join(localdata, "go-build"),                                 False, "dev")
    add("Nuget Cache",           os.path.join(localdata, "NuGet",   "Cache"),                         False, "dev")

    # JetBrains — per-product caches/log ONLY (never the JetBrains root or product root)
    jb_root = os.path.join(localdata, "JetBrains")
    if os.path.isdir(jb_root):
        for product in os.listdir(jb_root):
            product_path = os.path.join(jb_root, product)
            if not os.path.isdir(product_path):
                continue
            for cache_sub in ("caches", "log"):
                cache_path = os.path.join(product_path, cache_sub)
                if os.path.isdir(cache_path) and _is_safe_target(cache_path):
                    targets.append(_Target(f"JetBrains {product[:14]}/{cache_sub}", cache_path, False, "dev"))

    return targets


# ── Scan / clean helpers ──────────────────────────────────────────────────────

def _scan_dir(path: str) -> tuple[int, int]:
    """Return (total_bytes, file_count) — never raises."""
    total, count = 0, 0
    try:
        for root, _, files in os.walk(path, onerror=None):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                    count += 1
                except OSError:
                    pass
    except OSError:
        pass
    return total, count


def _clean_dir(path: str) -> tuple[int, int]:
    """Delete all contents (not the dir itself). Returns (bytes_freed, files_deleted)."""
    freed, deleted = 0, 0
    if not _is_safe_target(path):
        return 0, 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    size = entry.stat().st_size
                    os.remove(entry.path)
                    freed   += size
                    deleted += 1
                elif entry.is_dir(follow_symlinks=False):
                    size, count = _scan_dir(entry.path)
                    shutil.rmtree(entry.path, ignore_errors=True)
                    freed   += size
                    deleted += count
            except (OSError, PermissionError):
                pass
    except (OSError, PermissionError):
        pass
    return freed, deleted


def _cat_color(cat: str) -> str:
    return {"system": "blue", "browser": "magenta", "dev": "cyan"}.get(cat, "white")


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    """Structured scan data — no side effects, safe to call any time."""
    items: list[dict] = []
    total_bytes = total_files = skipped = 0
    for t in _build_targets():
        if not os.path.exists(t.path):
            continue
        if t.admin_only and not is_admin:
            skipped += 1
            continue
        size, count = _scan_dir(t.path)
        if size > 0 or count > 0:
            items.append({
                "name":       t.name,
                "path":       t.path,
                "category":   t.category,
                "size_bytes": size,
                "size_human": human_size(size),
                "files":      count,
                "admin_only": t.admin_only,
            })
            total_bytes += size
            total_files += count
    return {
        "total_bytes":   total_bytes,
        "total_files":   total_files,
        "total_human":   human_size(total_bytes),
        "targets":       items,
        "skipped_admin": skipped,
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "CACHE & TEMP CLEANER", "browser · dev · system")

    targets = _build_targets()
    results: list[tuple[_Target, int, int, bool]] = []  # (target, bytes, files, skipped)

    with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"),
                  console=console, transient=False) as prog:
        task = prog.add_task("Scanning…", total=len(targets))
        for t in targets:
            prog.update(task, description=f"Scanning  {t.name}")
            if not os.path.exists(t.path):
                prog.advance(task)
                continue
            if t.admin_only and not is_admin:
                results.append((t, 0, 0, True))
                prog.advance(task)
                continue
            size, count = _scan_dir(t.path)
            if size > 0 or count > 0:
                results.append((t, size, count, False))
            prog.advance(task)
    console.print()

    if not results:
        console.print("[dim]  Nothing found to clean.[/]\n")
        return

    # ── Scan table ────────────────────────────────────────────────────────────
    tbl = Table(box=box.SIMPLE, header_style="bold cyan", padding=(0, 1))
    tbl.add_column("Cat",    style="dim",     width=8)
    tbl.add_column("Target",                  width=24)
    tbl.add_column("Path",   style="dim",     width=40)
    tbl.add_column("Size",   justify="right", width=10)
    tbl.add_column("Files",  justify="right", width=7)
    tbl.add_column("",                        width=14)

    total_bytes = total_files = 0

    for t, size, count, skipped in results:
        cat_label = f"[{_cat_color(t.category)}]{t.category}[/]"
        short_path = t.path.replace(os.environ.get("USERPROFILE", "~"), "~")[:38]
        if skipped:
            tbl.add_row(cat_label, t.name, short_path, "[dim]—[/]", "[dim]—[/]", "[dim]needs admin[/]")
        else:
            tbl.add_row(cat_label, t.name, short_path,
                        f"[bold]{human_size(size)}[/]", f"{count:,}", "[green]cleanable[/]")
            total_bytes += size
            total_files += count

    console.print(tbl)
    console.print(f"\n  Cleanable: [bold green]{human_size(total_bytes)}[/]  ({total_files:,} files)")
    if not is_admin:
        console.print("  [dim]Run as Administrator to also clean system/prefetch targets.[/]")
    console.print()

    if total_bytes == 0:
        return

    if not auto_confirm:
        if not Confirm.ask("  [bold]Proceed with cleaning?[/]", default=False):
            console.print("  [dim]Cancelled.[/]")
            return

    # ── Clean ─────────────────────────────────────────────────────────────────
    total_freed = total_deleted = 0
    cleanable   = [r for r in results if not r[3]]

    with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"),
                  BarColumn(), TextColumn("{task.percentage:>3.0f}%"),
                  console=console) as prog:
        task = prog.add_task("Cleaning…", total=len(cleanable))
        for t, *_ in cleanable:
            prog.update(task, description=f"Cleaning  {t.name}")
            freed, deleted = _clean_dir(t.path)
            total_freed   += freed
            total_deleted += deleted
            prog.advance(task)

    console.print(
        f"\n  [bold green]Done.[/]  "
        f"{human_size(total_freed)} freed · {total_deleted:,} files removed.\n"
    )
