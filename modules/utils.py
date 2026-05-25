"""Shared utilities for all modules."""
from __future__ import annotations
import os
from rich.console import Console
from rich.panel import Panel
from rich import box


def human_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} PB"


def section_header(console: Console, title: str, subtitle: str = "") -> None:
    label = f"[bold cyan]{title}[/]"
    if subtitle:
        label += f"  [dim]{subtitle}[/]"
    console.print(Panel(label, box=box.ROUNDED, expand=False))
    console.print()


def status_icon(ok: bool) -> str:
    return "[bold green]✔[/]" if ok else "[bold red]✘[/]"
