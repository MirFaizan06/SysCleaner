# SysCleaner

**Windows system utility by Tech Bytes Design**

A professional, minimal, and powerful Windows cleaner and health tool built for both everyday users and AI agents.

---

## Features

| Module | What it does |
|--------|-------------|
| **Cache Cleaner** | Removes browser caches (Chrome, Edge, Brave, Firefox), dev tool caches (npm, Yarn, pnpm, pip, VS Code, JetBrains, Gradle, Cargo…), Windows Temp, Prefetch, thumbnail cache |
| **Network Refresh** | Flushes DNS, resets Winsock and TCP/IP stack (admin), shows adapter stats |
| **RAM Optimizer** | Displays live RAM stats; purges the standby memory list (admin) to recover unused cached pages |
| **System Info** | CPU name/cores/frequency/usage, RAM, all disks, OS version + build, uptime, battery |
| **Error Logs** | Last 10 Critical/Error/Warning entries from Windows System and Application event logs |
| **Threat Scan** | Checks running processes against known-bad names, lists startup programs, inspects hosts file, flags suspicious listening ports |
| **Smart Tips** | Contextual recommendations based on disk usage, RAM load, uptime, temp folder size, CPU load, and battery |

---

## Quick Start

### Run from source

```bash
pip install -r requirements.txt
python main.py
```

### Run as Administrator (for full functionality)

Right-click `run.bat` → **Run as administrator**

---

## Interactive Menu

```
  Select option: 1   →  Clean caches
                 2   →  Refresh network
                 3   →  Optimize RAM
                 4   →  System information
                 5   →  View error logs
                 6   →  Threat scan
                 7   →  Tips & recommendations
                 8   →  Full system report (all modules)
                 0   →  Exit
```

---

## CLI / Agent Mode

SysCleaner supports non-interactive execution — ideal for automation and AI agents.

```bash
# System info as JSON (safe, no changes)
python main.py info -j

# Full scan as JSON
python main.py all -j

# Clean without confirmation prompt
python main.py clean -y

# Run multiple modules
python main.py threats logs tips

# Full report auto-confirmed
python main.py all -y
```

| Flag | Meaning |
|------|---------|
| `-y` / `--yes` | Skip all confirmation prompts |
| `-j` / `--json` | Output structured JSON to stdout |

See [CLAUDE.md](CLAUDE.md) for the complete JSON schema and AI agent guide.

---

## Build (EXE + Installer)

```bash
build.bat
```

This runs four steps automatically:

1. Installs `rich`, `psutil`, `pillow`, `pyinstaller`
2. Generates `syscleaner.ico` (brand icon)
3. Builds `dist/SysCleaner.exe` via PyInstaller
4. Compiles `dist/installer/SysCleaner_Setup_v1.0.0.exe` via Inno Setup

**Requirements:** Python 3.10+, Inno Setup 6 at `C:\Program Files (x86)\Inno Setup 6\`

---

## Safety

- **Only explicitly whitelisted paths** are ever scanned or cleaned — no user input accepted as a path.
- **Firefox:** Only `cache2`, `thumbnails`, and `OfflineCache` inside each profile are touched — never the profile root (which holds bookmarks, passwords, history).
- **JetBrains:** Only `caches` and `log` within each product version directory — never the product root (which holds settings and workspace data).
- **No auto-delete** — cleaning always requires confirmation unless `-y` flag is passed.
- **Admin-only operations** are clearly labelled and gracefully skipped in user mode.
- A `_is_safe_target()` guard double-checks every path before any file is touched.

---

## Requirements

```
rich>=13.7.0
psutil>=6.0.0
```

Python 3.10 or newer, Windows 10/11 only.

---

## Tech Bytes Design

Professional web and software development agency.  
Website: [techbytesdesign.in](https://techbytesdesign.in)
