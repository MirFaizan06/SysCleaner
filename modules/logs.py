"""Windows Event Log viewer — last 5 critical/error/warning entries."""
from __future__ import annotations
import subprocess
import re
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich import box

from modules.utils import section_header


LEVEL_STYLE = {
    "Critical": "bold red",
    "Error":    "red",
    "Warning":  "yellow",
}

LEVEL_QUERY = "(Level=1 or Level=2 or Level=3)"   # Critical / Error / Warning


@dataclass
class _Event:
    channel: str
    time: str
    level: str
    source: str
    event_id: str
    description: str


def _fetch(channel: str, count: int) -> list[_Event]:
    query = f"*[System[{LEVEL_QUERY}]]"
    try:
        result = subprocess.run(
            ["wevtutil", "qe", channel,
             f"/q:{query}", f"/c:{count}",
             "/rd:true", "/f:text"],
            capture_output=True, text=True, timeout=20,
            encoding="utf-8", errors="replace",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0 or not result.stdout.strip():
        return []

    events: list[_Event] = []
    current: dict[str, str] = {}
    desc_lines: list[str]   = []
    in_desc = False

    for line in result.stdout.splitlines():
        stripped = line.strip()

        if re.match(r"^Event\[\d+\]:", stripped):
            if current:
                current["description"] = " ".join(desc_lines).strip()[:220]
                events.append(_parse_event(channel, current))
            current   = {}
            desc_lines = []
            in_desc    = False
            continue

        if in_desc:
            if stripped:
                desc_lines.append(stripped)
            continue

        if ":" in stripped and not in_desc:
            key, _, val = stripped.partition(":")
            key = key.strip().lower().replace(" ", "_")
            val = val.strip()
            if key == "description":
                in_desc = True
                if val:
                    desc_lines.append(val)
            else:
                current[key] = val

    if current:
        current["description"] = " ".join(desc_lines).strip()[:220]
        events.append(_parse_event(channel, current))

    return events


def _parse_event(channel: str, d: dict[str, str]) -> _Event:
    level_map = {"1": "Critical", "2": "Error", "3": "Warning",
                 "critical": "Critical", "error": "Error", "warning": "Warning"}
    raw_level = d.get("level", "").strip()
    level     = level_map.get(raw_level.lower(), raw_level.capitalize() or "Info")
    return _Event(
        channel     = channel,
        time        = d.get("date", ""),
        level       = level,
        source      = d.get("source", ""),
        event_id    = d.get("event_id", ""),
        description = d.get("description", ""),
    )


# ── Public API ────────────────────────────────────────────────────────────────

def report(is_admin: bool = False) -> dict:
    events = _fetch("System", 5) + _fetch("Application", 5)
    events = sorted(events, key=lambda e: e.time, reverse=True)[:10]
    return {
        "events": [
            {"channel": e.channel, "time": e.time, "level": e.level,
             "source": e.source, "event_id": e.event_id, "description": e.description}
            for e in events
        ]
    }


def run(console: Console, is_admin: bool = False, auto_confirm: bool = False) -> None:
    section_header(console, "RECENT ERROR LOGS", "System + Application channels")

    all_events: list[_Event] = []
    for channel in ("System", "Application"):
        all_events.extend(_fetch(channel, 5))

    if not all_events:
        console.print("  [dim]No events found (wevtutil unavailable or log is empty).[/]\n")
        return

    # Sort newest-first (alphabetical works for the ISO-like date strings wevtutil returns)
    all_events.sort(key=lambda e: e.time, reverse=True)
    events = all_events[:10]

    tbl = Table(box=box.SIMPLE, header_style="bold cyan", show_header=True, padding=(0, 1))
    tbl.add_column("Time",      width=22)
    tbl.add_column("Ch",        width=5,  style="dim")
    tbl.add_column("Level",     width=10)
    tbl.add_column("ID",        width=6,  justify="right", style="dim")
    tbl.add_column("Source",    width=28)
    tbl.add_column("Message",   width=50)

    for ev in events:
        style    = LEVEL_STYLE.get(ev.level, "white")
        ch_short = ev.channel[:3].upper()
        desc     = ev.description[:80] + ("…" if len(ev.description) > 80 else "")
        tbl.add_row(
            ev.time,
            ch_short,
            f"[{style}]{ev.level}[/]",
            ev.event_id,
            ev.source[:28],
            f"[dim]{desc}[/]",
        )

    console.print(tbl)
    console.print()
