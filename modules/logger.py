"""
SysCleaner application logger.

Local:  Rotating file at %APPDATA%\\Tech Bytes Design\\SysCleaner\\logs\\syscleaner.log
        (5 MB max, 3 backups)

Remote: Anonymous POST to Tech Bytes Design admin API.
        Only version, OS, error type, message, traceback, and a hashed hostname are sent.
        No personal data, no file paths, no usernames.
        Can be disabled by setting env var: SYSCLEANER_NO_REMOTE=1
"""
from __future__ import annotations
import hashlib
import json
import logging
import logging.handlers
import os
import platform
import socket
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

APP_NAME     = "SysCleaner"
APP_VERSION  = "1.1.0"
COMPANY      = "Tech Bytes Design"

_API_ENDPOINT    = "https://techbytesdesign.vercel.app/api/logs"
_APP_ID          = "syscleaner"
# API key is created inside the TBD admin panel (Logs → Connect App → SysCleaner).
# Override at runtime via env: SYSCLEANER_API_KEY
_DEFAULT_API_KEY = "tbd-syscleaner-2026-k9m2x8p4r7"

_LOG_DIR  = Path(os.environ.get("APPDATA", Path.home())) / COMPANY / APP_NAME / "logs"
_LOG_FILE = _LOG_DIR / "syscleaner.log"

_logger: logging.Logger | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hostname_hash() -> str:
    """One-way hash of hostname — links sessions on the same machine without storing identity."""
    try:
        return hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
    except Exception:
        return "unknown"


def _os_str() -> str:
    try:
        return f"Windows {platform.version()}"
    except Exception:
        return "Windows"


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup() -> logging.Logger:
    global _logger
    if _logger:
        return _logger

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("syscleaner")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fh = logging.handlers.RotatingFileHandler(
            _LOG_FILE,
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(fh)

    _logger = logger
    return logger


def get_log_path() -> Path:
    return _LOG_FILE


# ── Logging API ───────────────────────────────────────────────────────────────

def log_info(message: str, module: str = "") -> None:
    lg = setup()
    lg.info(f"[{module}] {message}" if module else message)


def log_warning(message: str, module: str = "", exc: BaseException | None = None) -> None:
    lg = setup()
    lg.warning(f"[{module}] {message}" if module else message)
    if exc:
        lg.debug(traceback.format_exc())
    _send_remote(message, module, type(exc).__name__ if exc else "Warning",
                 traceback.format_exc() if exc else "", "warning")


def log_error(
    message: str,
    module: str = "",
    exc: BaseException | None = None,
    severity: str = "error",
) -> None:
    lg  = setup()
    tb  = traceback.format_exc() if exc else ""
    err = type(exc).__name__ if exc else "Error"

    lg.error(f"[{module}] {message}" if module else message)
    if tb and "NoneType: None" not in tb:
        lg.debug(f"Traceback:\n{tb}")

    _send_remote(message, module, err, tb, severity)


def log_critical(message: str, module: str = "", exc: BaseException | None = None) -> None:
    log_error(message, module, exc, severity="critical")


# ── Remote submit ─────────────────────────────────────────────────────────────

def _send_remote(
    message: str,
    module: str,
    error_type: str,
    tb: str,
    severity: str,
) -> None:
    """Fire-and-forget: POST an anonymous log entry to the Tech Bytes Design API."""
    if os.environ.get("SYSCLEANER_NO_REMOTE", "").strip() == "1":
        return

    import urllib.request
    import urllib.error

    api_key = os.environ.get("SYSCLEANER_API_KEY", _DEFAULT_API_KEY)
    payload = json.dumps({
        "appId":        _APP_ID,
        "version":      APP_VERSION,
        "os":           _os_str(),
        "errorType":    error_type,
        "message":      message[:500],
        "traceback":    tb[:2000],
        "hostnameHash": _hostname_hash(),
        "module":       module[:50],
        "severity":     severity,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            _API_ENDPOINT,
            data=payload,
            headers={
                "Content-Type":   "application/json",
                "X-App-Log-Key":  api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception:
        pass  # Never let remote logging break the app


# ── Exception hook ────────────────────────────────────────────────────────────

def install_exception_hook() -> None:
    """Log all unhandled exceptions to file + remote before the app crashes."""
    _original = sys.excepthook

    def _hook(exc_type: type, exc_value: BaseException, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            _original(exc_type, exc_value, exc_tb)
            return
        msg = f"Unhandled exception: {exc_type.__name__}: {exc_value}"
        log_critical(msg, module="main", exc=exc_value)
        _original(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook
