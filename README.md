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

## Website Long Description

> **Copy the block below into the Firestore `projects/{id}.longDescription` field via the admin panel.**

---

```markdown
## What is SysCleaner?

SysCleaner is a free, open-source Windows system maintenance utility built by Tech Bytes Design. It gives you a single command — or an interactive menu — to clean junk files, refresh your network stack, inspect your RAM, review Windows event logs, and run a basic threat scan, all without installing any heavy software or bloating your system with background services.

It is built for two audiences: everyday Windows users who want a trustworthy tool that won't accidentally delete anything important, and AI agents or automation scripts that need structured, machine-readable system data.

---

## Features

### Cache & Temp Cleaner
Removes gigabytes of redundant cache files from the most common sources on a Windows machine — browser caches (Chrome, Edge, Brave, Opera, Firefox), development tool caches (npm, Yarn, pnpm, pip, uv, VS Code extensions, JetBrains IDEs, Gradle, Docker, Cargo, Go module cache, NuGet, Composer), and system-level temps (Windows Temp, Prefetch, WER crash reports, thumbnail database, D3D shader cache).

The cleaner never blindly deletes. Every path is validated against a strict whitelist before anything is touched. Firefox profiles are handled per-profile — only `cache2`, `thumbnails`, and `OfflineCache` are removed, never the profile root that stores your bookmarks, saved passwords, and browsing history. JetBrains IDEs are handled similarly: only `caches` and `log` inside each product version directory, never the workspace or settings.

### Network Refresh
Flushes the DNS resolver cache, resets the Winsock catalog, and resets the TCP/IP stack (the latter two require Administrator). After a reset it verifies internet connectivity and shows a summary of all active network adapters including their IP addresses and current sent/received traffic.

### RAM Optimizer
Displays live RAM usage (total, used, free, percent). When run as Administrator, it invokes the Windows `NtSetSystemInformation` API to purge the standby memory list — RAM that Windows is holding in a "soft" cached state. This instantly recovers that memory for use by applications without any risk to running processes.

### System Information
Shows a complete snapshot: CPU model, physical and logical core count, current clock speed and load percentage; RAM totals; all mounted disks with free space and usage percent; OS edition and Windows build number; system uptime; and battery status if applicable.

### Windows Event Log Viewer
Reads the last 10 Critical, Error, and Warning entries from both the System and Application Windows Event Log channels using the built-in `wevtutil` command-line tool. Each entry shows the timestamp, event ID, source, log level, and the first line of the description.

### Threat Scanner
A lightweight heuristic scan that checks:
- Running processes against a list of known-bad names (cryptominers, RATs, credential dumpers, ransomware indicators)
- Windows startup entries from the registry (`HKLM` and `HKCU` Run keys) and the Startup folder
- The hosts file for suspicious non-local IP redirects
- Open listening ports flagged as commonly abused (Metasploit defaults, common C2 ports, etc.)

This is not a replacement for Windows Defender. It is a quick first-look heuristic.

### Smart Tips
Generates contextual recommendations based on live system state: disk usage above thresholds, high RAM pressure, very long uptime, oversized temp folder, sustained high CPU, and battery health. General best-practice tips are also included.

---

## CLI and AI Agent Mode

SysCleaner ships with a full headless mode designed for automation and AI agents. Pass any combination of command names and the `-y` (auto-confirm) and `-j` (JSON output) flags:

```bash
# Safe read-only snapshot as JSON
python main.py info logs threats tips -j

# Full clean, network refresh, RAM purge — no prompts
python main.py all -y

# Just the threat scan in JSON
python main.py threats -j
```

The JSON schema is fully documented in `CLAUDE.md` so that any AI assistant can read the tool, understand the output format, and act on the results.

---

## Remote Error Logging

SysCleaner integrates with the Tech Bytes Design logging infrastructure. When an unexpected error occurs, it sends an anonymous report to our servers — no usernames, no file paths, no personal data. The payload contains only: the error type, a one-line message, a stack trace, the Windows version string, the app version, and a one-way SHA-256 hash of the machine hostname (for correlating crashes from the same device without identifying the user).

Remote logging can be disabled entirely by setting the environment variable `SYSCLEANER_NO_REMOTE=1`. All logs are also written locally to `%APPDATA%\Tech Bytes Design\SysCleaner\logs\syscleaner.log` with a 5 MB rotating limit and 3 backup files.

---

## Safety First

Every design decision in the cleaner prioritises safety:

- **Whitelist-only**: no user-supplied paths, no glob patterns that could escape intended directories
- **Depth check**: rejects any path with fewer than 4 components to prevent accidental top-level deletions
- **Explicit allowlist for system paths**: `C:\Windows\Temp` and `C:\Windows\Prefetch` are the only Windows directories explicitly permitted
- **Per-profile Firefox handling**: targets only cache subdirectories within each profile, never the profile root
- **Confirmation gate**: interactive mode always asks before deleting; the `-y` flag is required to skip it

---

## Tech Stack

Built entirely on the Python standard library plus two dependencies:

- **Rich** — terminal UI (tables, panels, progress bars, colour)
- **psutil** — cross-platform system metrics

The standalone Windows EXE is built with PyInstaller and distributed via an Inno Setup installer — no Python installation required on the end-user machine.
```

---

## Tech Bytes Design

Professional web and software development agency.  
Website: [techbytesdesign.in](https://techbytesdesign.in)
