from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


_PID_FILE = Path.home() / ".seiautomation-devserver.pid"


def _read_pid() -> int | None:
    try:
        pid = int(_PID_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None
    return pid


def _write_pid(pid: int) -> None:
    _PID_FILE.write_text(str(pid))


def _clear_pid() -> None:
    try:
        _PID_FILE.unlink()
    except FileNotFoundError:
        pass


def is_devserver_running() -> bool:
    pid = _read_pid()
    if not pid:
        return False
    try:
        # os.kill with signal 0 only checks if process exists (POSIX / Windows 3.9+)
        os.kill(pid, 0)
    except OSError:
        _clear_pid()
        return False
    return True


def start_devserver(host: str = "127.0.0.1", port: int = 8001) -> bool:
    if is_devserver_running():
        return True

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    _write_pid(proc.pid)

    # Give uvicorn a moment to start
    time.sleep(1.0)
    return True


def stop_devserver() -> bool:
    pid = _read_pid()
    if not pid:
        return False
    try:
        if sys.platform.startswith("win"):
            os.kill(pid, signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    _clear_pid()
    return True

