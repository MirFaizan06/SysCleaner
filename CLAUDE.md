# SysCleaner — AI Agent Guide

**Product:** Tech Bytes Design SysCleaner v1.1.0  
**Purpose:** Windows system utility — cache cleaning, network refresh, RAM optimization, disk analysis, startup management, HTML reports, event logs, threat scan, smart tips.  
**Runtime:** Python 3.10+, Windows 10/11 only.  
**CLI command:** `sysc` (installed to PATH by the installer) or `python main.py`

---

## How to run (as an AI agent)

### Prerequisites

```bash
pip install -r requirements.txt
```

### Command syntax

```
sysc [command ...] [-y] [-j]
```

| Flag | Meaning |
|------|---------|
| `-y` / `--yes` | Skip confirmation prompts (required for non-interactive / agent use) |
| `-j` / `--json` | Return structured JSON instead of Rich terminal output |

### Available commands

| Command | What it does |
|---------|--------------|
| `info` | CPU, RAM, disk, OS, uptime — no side effects |
| `clean` | Scan and delete cached/temp files (asks confirmation unless `-y`) |
| `network` | Flush DNS, reset Winsock (admin), show adapter info |
| `ram` | RAM stats; purge standby memory if admin |
| `disk` | Disk space analyzer — drive usage + top folders by size |
| `startup` | Startup manager — list and toggle startup entries |
| `logs` | Last 10 critical/error/warning entries from System + Application event logs |
| `threats` | Heuristic scan: known-bad processes, startup items, hosts file, suspicious ports |
| `tips` | Contextual recommendations based on live system state |
| `report` | Generate a self-contained HTML system report saved to ~/Documents/SysCleaner Reports/ |
| `all` | Run every command in sequence (except report) |

---

## Typical agent workflows

### 1. Read system state (safe, no changes)

```bash
sysc info logs threats tips -j
```

Returns JSON with four top-level keys: `info`, `logs`, `threats`, `tips`.

### 2. Full clean + refresh (non-interactive)

```bash
sysc all -y
```

Runs every module. Cleaning is auto-confirmed. Network and RAM ops require Administrator for full effect.

### 3. Just clean caches silently

```bash
sysc clean -y
```

### 4. Check for threats only

```bash
sysc threats -j
```

Inspect `result["threats"]["risk_level"]` — values: `"low"`, `"medium"`, `"high"`.

### 5. Analyze disk space

```bash
sysc disk -j
```

Returns drive-level stats + top folders by size.

### 6. View startup programs

```bash
sysc startup -j
```

Returns all startup entries with enabled/disabled status. Toggle disabled in interactive mode.

### 7. Generate HTML report

```bash
sysc report
```

Collects data from all modules and saves a self-contained HTML file to `~/Documents/SysCleaner Reports/`. Opens automatically in the default browser.

---

## JSON schema (key fields)

### `info`
```json
{
  "os": "string",
  "hostname": "string",
  "uptime": "3d 4h 12m",
  "cpu": { "name": "...", "cores_phys": 8, "cores_logic": 16, "freq_mhz": 2300, "usage_pct": 12.3 },
  "ram": { "total_bytes": 17179869184, "used_bytes": 9000000000, "free_bytes": 8000000000, "percent": 52.4 },
  "disks": [ { "device": "C:\\", "total_bytes": 255, "free_bytes": 50, "percent": 79 } ],
  "battery": { "percent": 85, "plugged_in": true }
}
```

### `clean`
```json
{
  "total_bytes": 1234567890,
  "total_files": 8432,
  "total_human": "1.1 GB",
  "targets": [ { "name": "Chrome Cache", "category": "browser", "size_bytes": 94371840, "files": 456 } ],
  "skipped_admin": 2
}
```

### `disk`
```json
{
  "drives": [
    { "device": "C:\\", "fstype": "NTFS", "total_bytes": 274877906944,
      "used_bytes": 150000000000, "free_bytes": 124877906944, "percent": 54.6 }
  ],
  "top_dirs": [
    { "label": "AppData\\Local", "path": "C:\\Users\\...", "bytes": 20000000000 }
  ]
}
```

### `startup`
```json
{
  "count": 14,
  "enabled": 12,
  "entries": [
    { "idx": 0, "hive": "HKCU", "name": "Discord", "command": "C:\\...\\Discord.exe --processStart", "enabled": true }
  ]
}
```

### `threats`
```json
{
  "risk_level": "low",
  "total_processes": 148,
  "bad_processes": [],
  "startup_count": 12,
  "hosts_suspicious": [],
  "suspicious_ports": []
}
```

### `logs`
```json
{
  "events": [
    { "channel": "System", "time": "5/25/2026 10:30 AM", "level": "Error",
      "source": "Service Control Manager", "event_id": "7034", "description": "..." }
  ]
}
```

---

## Admin vs. user mode

Many operations are more effective when the process runs as Administrator:

| Feature | User | Admin |
|---------|------|-------|
| Clean Windows Temp & Prefetch | ✘ | ✔ |
| Flush DNS | ✔ | ✔ |
| Reset Winsock / TCP stack | ✘ | ✔ |
| Purge standby RAM | ✘ | ✔ |
| Toggle HKLM startup entries | ✘ | ✔ |

In interactive mode (no CLI flags), SysCleaner prompts to re-launch with UAC elevation automatically.

To run as admin from PowerShell:
```powershell
Start-Process SysCleaner.exe -Verb RunAs
# or from source:
Start-Process python -ArgumentList "main.py all -y" -Verb RunAs
```

---

## Notes for AI agents

- `clean -y` is **destructive but safe** — only removes cache and temp files, never user documents.
- `network` with Winsock/TCP reset: notifies about reboot requirement in output but does not reboot automatically.
- `threats` is a **heuristic scan only** — not a replacement for Windows Defender.
- `startup` toggle in non-interactive (`-y`) mode: lists entries only, does not modify anything.
- `report` command opens the HTML file automatically in the default browser after saving.
- All modules catch exceptions individually; a failure in one module does not crash others.
- JSON output uses `default=str` for non-serializable types (e.g., datetime). Parse defensively.
- Export files land in `~/Documents/SysCleaner/exports/` as `syscleaner_<cmd>_<timestamp>.[json|txt]`.
- HTML reports land in `~/Documents/SysCleaner Reports/SysCleaner_Report_<timestamp>.html`.
