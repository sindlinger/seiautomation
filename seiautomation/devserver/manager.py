from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse


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


def _parse_base_url(base_url: str | None) -> tuple[str, int]:
    if not base_url:
        return "127.0.0.1", 8001
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    scheme = parsed.scheme or "http"
    port = parsed.port or (443 if scheme == "https" else 8001)
    return host, port


def is_devserver_running(base_url: str | None = None) -> bool:
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


def start_devserver(base_url: str | None = None) -> tuple[bool, str, bool]:
    host, port = _parse_base_url(base_url)
    if is_devserver_running(base_url):
        return False, f"Servidor fake já em execução em {host}:{port}.", False

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

    try:
        proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
        )
    except FileNotFoundError:
        return False, "Não foi possível iniciar uvicorn. Verifique se as dependências do backend estão instaladas.", False
    _write_pid(proc.pid)

    # Give uvicorn a moment to start
    time.sleep(1.0)
    return True, f"Servidor fake iniciado em {host}:{port}.", True


def stop_devserver(base_url: str | None = None) -> tuple[bool, str, bool]:
    pid = _read_pid()
    if not pid:
        return False, "Servidor fake não está em execução.", False
    try:
        if sys.platform.startswith("win"):
            os.kill(pid, signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    _clear_pid()
    host, port = _parse_base_url(base_url)
    return True, f"Servidor fake finalizado em {host}:{port}.", True
