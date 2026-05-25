# SysCleaner

**Windows system utility by Tech Bytes Design — v1.1.0**

A professional, minimal, and powerful Windows cleaner and health tool built for both everyday users and AI agents.

---

## Features

| Module | What it does |
|--------|-------------|
| **Cache Cleaner** | Removes browser caches (Chrome, Edge, Brave, Firefox), dev tool caches (npm, Yarn, pnpm, pip, VS Code, JetBrains, Gradle, Cargo…), Windows Temp, Prefetch, thumbnail cache |
| **Network Refresh** | Flushes DNS, resets Winsock and TCP/IP stack (admin), shows adapter stats |
| **RAM Optimizer** | Displays live RAM stats; purges the standby memory list (admin) to recover unused cached pages |
| **System Info** | CPU name/cores/frequency/usage, RAM, all disks, OS version + build, uptime, battery |
| **Disk Analyzer** | Scans common directories and shows top space consumers with visual bars |
| **Startup Manager** | Lists all startup programs (registry + folder); toggle entries on/off without deleting them |
| **Error Logs** | Last 10 Critical/Error/Warning entries from Windows System and Application event logs |
| **Threat Scan** | Checks running processes against known-bad names, lists startup programs, inspects hosts file, flags suspicious listening ports |
| **Smart Tips** | Contextual recommendations based on disk usage, RAM load, uptime, temp folder size, CPU load, and battery |
| **HTML Report** | Generates a beautiful, self-contained HTML system report saved to `~/Documents/SysCleaner Reports/` — opens automatically in your browser |

---

## Quick Start

### Installed (after running the installer)

```bash
sysc              # interactive menu
sysc info         # system info
sysc clean -y     # clean without prompts
sysc report       # generate HTML report
```

### Run from source

```bash
pip install -r requirements.txt
python main.py
```

### Run as Administrator (for full functionality)

Right-click `SysCleaner.exe` → **Run as administrator**  
Or: SysCleaner will prompt you to elevate via UAC when you launch it interactively.

---

## Interactive Menu

```
  MAINTENANCE
  ──────────────────────────────────────────────────────────────────
   1   Clean Caches & Temp Files      browser · dev tools · windows temp
   2   Refresh Network                DNS flush · winsock reset · adapters
   3   Optimize RAM                   live stats · standby memory purge

  DIAGNOSTICS
  ──────────────────────────────────────────────────────────────────
   4   System Information             CPU · RAM · disk · OS · uptime
   5   Disk Analyzer                  top folders by size · drive usage
   6   Startup Manager                view · enable · disable startup entries
   7   View Error Logs                last 10 critical/error/warning events
   8   Threat Scan                    processes · startup · hosts · ports
   9   Tips & Recommendations         smart advice based on your system

  ──────────────────────────────────────────────────────────────────
   R   Generate HTML Report           full snapshot saved to Documents
   A   Run All Modules                maintenance + diagnostics in sequence
   0   Exit
```

---

## CLI / Agent Mode

SysCleaner supports non-interactive execution — ideal for automation and AI agents.

```bash
# System info as JSON (safe, no changes)
sysc info -j

# Full scan as JSON
sysc all -j

# Clean without confirmation prompt
sysc clean -y

# Analyze disk space
sysc disk -j

# List startup entries
sysc startup -j

# Generate HTML report
sysc report

# Run multiple modules
sysc threats logs tips

# Full run auto-confirmed
sysc all -y
```

| Flag | Meaning |
|------|---------|
| `-y` / `--yes` | Skip all confirmation prompts |
| `-j` / `--json` | Output structured JSON to stdout |

See [CLAUDE.md](CLAUDE.md) for the complete JSON schema and AI agent guide.

---

## Export Feature

After running diagnostics (info, disk, logs, threats, startup) in interactive mode, SysCleaner offers to export the results:

```
  Save results?  [j=JSON  t=TXT  Enter=skip]
```

Exports are saved to `~/Documents/SysCleaner/exports/`. Useful for:
- Sending to IT support
- AI-assisted analysis
- Keeping a system audit trail

---

## HTML System Report

Run `sysc report` (or press **R** in the menu) to generate a complete, self-contained HTML report:

- System overview (CPU, RAM, uptime, battery)
- All drive usage with progress bars
- Threat scan summary
- Windows event log entries
- All startup programs (enabled/disabled)
- Smart recommendations

Saved to `~/Documents/SysCleaner Reports/`. Opens automatically in your default browser. Supports light and dark mode.

---

## Build (EXE + Installer)

```bash
build.bat
```

This runs four steps automatically:

1. Installs `rich`, `psutil`, `pillow`, `pyinstaller`
2. Generates `syscleaner.ico` (brand icon)
3. Builds `dist/SysCleaner.exe` via PyInstaller
4. Compiles `dist/installer/SysCleaner_Setup_v1.1.0.exe` via Inno Setup

**Requirements:** Python 3.10+, Inno Setup 6 at `C:\Program Files (x86)\Inno Setup 6\`

The installer:
- Adds the install directory to PATH so `sysc` works from any terminal
- Installs `sysc.cmd` wrapper alongside `SysCleaner.exe`
- Creates Start Menu and optional Desktop shortcuts
- Prompts to re-install cleanly over v1.0.0

---

## Safety

- **Only explicitly whitelisted paths** are ever scanned or cleaned — no user input accepted as a path.
- **Firefox:** Only `cache2`, `thumbnails`, and `OfflineCache` inside each profile are touched — never the profile root (which holds bookmarks, passwords, history).
- **JetBrains:** Only `caches` and `log` within each product version directory — never the workspace or settings.
- **No auto-delete** — cleaning always requires confirmation unless `-y` flag is passed.
- **Admin-only operations** are clearly labelled and gracefully skipped in user mode.
- A `_is_safe_target()` guard double-checks every path before any file is touched.
- **Startup Manager:** Disabling entries only renames the registry value (adds `DISABLED_` prefix) — it never deletes anything and is fully reversible.

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

SysCleaner is a free, open-source Windows system maintenance utility built by Tech Bytes Design. It gives you a single command — or an interactive menu — to clean junk files, refresh your network stack, analyze disk usage, manage startup programs, generate a full HTML system report, inspect your RAM, review Windows event logs, and run a basic threat scan, all without installing any heavy software or bloating your system with background services.

It is built for two audiences: everyday Windows users who want a trustworthy tool that won't accidentally delete anything important, and AI agents or automation scripts that need structured, machine-readable system data.

---

## Features

### Cache & Temp Cleaner
Removes gigabytes of redundant cache files from the most common sources on a Windows machine — browser caches (Chrome, Edge, Brave, Opera, Firefox), development tool caches (npm, Yarn, pnpm, pip, uv, VS Code extensions, JetBrains IDEs, Gradle, Docker, Cargo, Go module cache, NuGet, Composer), and system-level temps (Windows Temp, Prefetch, WER crash reports, thumbnail database, D3D shader cache).

The cleaner never blindly deletes. Every path is validated against a strict whitelist before anything is touched. Firefox profiles are handled per-profile — only `cache2`, `thumbnails`, and `OfflineCache` are removed, never the profile root that stores your bookmarks, saved passwords, and browsing history.

### Network Refresh
Flushes the DNS resolver cache, resets the Winsock catalog, and resets the TCP/IP stack (the latter two require Administrator). After a reset it verifies internet connectivity and shows a summary of all active network adapters.

### RAM Optimizer
Displays live RAM usage (total, used, free, percent). When run as Administrator, it invokes the Windows `NtSetSystemInformation` API to purge the standby memory list — RAM that Windows is holding in a "soft" cached state. This instantly recovers that memory for use by applications without any risk to running processes.

### Disk Analyzer
Scans common directories (Downloads, Documents, Videos, AppData, Program Files, and more) and shows them ranked by size with visual usage bars. Helps you quickly identify what's eating your disk space so you know exactly where to clean.

### Startup Manager
Lists all programs configured to launch at Windows startup — from both the registry (`HKCU` and `HKLM` Run keys) and the Startup folder. Lets you toggle entries on or off with a single keypress. Disabling is safe and reversible: it only renames the registry value (adds a `DISABLED_` prefix) and never deletes anything.

### HTML System Report
Generates a beautiful, fully self-contained HTML file saved to `~/Documents/SysCleaner Reports/`. The report includes: system overview cards (CPU, RAM, uptime, battery), drive usage with progress bars, threat scan summary, Windows event log entries, startup program list, and smart recommendations. Supports light and dark mode automatically. No internet connection required to view it.

### System Information
Shows a complete snapshot: CPU model, physical and logical core count, current clock speed and load percentage; RAM totals; all mounted disks with free space and usage percent; OS edition and Windows build number; system uptime; and battery status if applicable.

### Windows Event Log Viewer
Reads the last 10 Critical, Error, and Warning entries from both the System and Application Windows Event Log channels using the built-in `wevtutil` command-line tool. Each entry shows the timestamp, event ID, source, log level, and description.

### Threat Scanner
A lightweight heuristic scan that checks running processes against a list of known-bad names (cryptominers, RATs, credential dumpers, ransomware indicators), Windows startup entries, the hosts file for suspicious non-local IP redirects, and open listening ports flagged as commonly abused.

### Smart Tips
Generates contextual recommendations based on live system state: disk usage above thresholds, high RAM pressure, very long uptime, oversized temp folder, sustained high CPU, and battery health.

---

## CLI and AI Agent Mode

SysCleaner ships with a full headless mode designed for automation and AI agents. Pass any combination of command names and the `-y` (auto-confirm) and `-j` (JSON output) flags:

```bash
# Safe read-only snapshot as JSON
sysc info logs threats tips -j

# Full clean, network refresh, RAM purge — no prompts
sysc all -y

# Disk space analysis
sysc disk -j

# Generate HTML report
sysc report
```

The JSON schema is fully documented in `CLAUDE.md` so that any AI assistant can read the tool, understand the output format, and act on the results.

---

## Export Feature

After running any diagnostic module interactively, SysCleaner offers to save the results as JSON or plain text — useful for sending to IT support, AI-assisted diagnosis, or keeping a system audit trail.

---

## Remote Error Logging

When an unexpected error occurs, SysCleaner sends an anonymous report to our servers — no usernames, no file paths, no personal data. The payload contains only: the error type, a one-line message, a stack trace, the Windows version string, the app version, and a one-way SHA-256 hash of the machine hostname. Remote logging can be disabled entirely by setting `SYSCLEANER_NO_REMOTE=1`.

---

## Tech Stack

Built on the Python standard library plus two dependencies: **Rich** (terminal UI) and **psutil** (system metrics). The standalone Windows EXE is built with PyInstaller and distributed via an Inno Setup installer — no Python installation required on the end-user machine.
```

---

## Tech Bytes Design

Professional web and software development agency.  
Website: [techbytesdesign.in](https://techbytesdesign.in)
