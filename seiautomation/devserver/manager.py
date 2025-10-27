from __future__ import annotations

import os
import signal
import socket
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
    host, port = _parse_base_url(base_url)
    if host not in {"127.0.0.1", "localhost"} or port != 8001:
        return _port_is_ready(host, port)

    pid = _read_pid()
    if not pid:
        return _port_is_ready(host, port)
    try:
        # os.kill with signal 0 only checks if process exists (POSIX / Windows 3.9+)
        os.kill(pid, 0)
    except OSError:
        _clear_pid()
        return False
    return True


def _port_is_ready(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def start_devserver(base_url: str | None = None) -> tuple[bool, str, bool]:
    host, port = _parse_base_url(base_url)
    if host not in {"127.0.0.1", "localhost"}:
        if _port_is_ready(host, port):
            return True, f"Servidor externo ativo em {host}:{port}.", False
        return False, "Não é possível iniciar automaticamente um servidor remoto.", False

    if port != 8001:
        return False, "A inicialização automática suporta apenas a porta local 8001.", False

    if is_devserver_running(base_url):
        return True, f"Servidor fake já em execução em {host}:{port}.", False

    cmd = [
        sys.executable,
        "-m",
        "seiautomation.devserver.app",
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
        return False, "Não foi possível iniciar o servidor fake. Verifique se o pacote está instalado.", False
    _write_pid(proc.pid)

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        if _port_is_ready(host, port):
            return True, f"Servidor fake iniciado em {host}:{port}.", True
        time.sleep(0.2)

    stop_devserver(base_url)
    return False, "Servidor fake não respondeu a tempo. Verifique logs e tente novamente.", False


def stop_devserver(base_url: str | None = None) -> tuple[bool, str, bool]:
    pid = _read_pid()
    if not pid:
        return False, "Servidor fake não está em execução.", False
    host, port = _parse_base_url(base_url)
    if host not in {"127.0.0.1", "localhost"}:
        return False, "Servidor remoto precisa ser finalizado manualmente.", False

    if port != 8001:
        return False, "Encerramento automático suportado apenas para a porta local 8001.", False

    try:
        if sys.platform.startswith("win"):
            os.kill(pid, signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        else:
            os.kill(pid, signal.SIGTERM)
        time.sleep(0.2)
    except OSError:
        pass
    _clear_pid()
    return True, "Servidor fake finalizado.", True
