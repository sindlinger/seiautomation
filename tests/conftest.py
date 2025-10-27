from __future__ import annotations

import multiprocessing
import socket
import time
from typing import Dict
from urllib import request as urllib_request

import pytest

from seiautomation.config import Settings
from seiautomation.devserver.app import run_devserver


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 5.0) -> None:
    start = time.time()
    last_err: Exception | None = None
    while time.time() - start < timeout:
        try:
            with urllib_request.urlopen(url, timeout=0.3):
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.1)
    raise RuntimeError(f"Servidor fake não iniciou em {timeout}s") from last_err


def _post(url: str, data: bytes | None = None) -> None:
    req = urllib_request.Request(url, data=data or b"", method="POST")
    with urllib_request.urlopen(req, timeout=0.5):
        pass


@pytest.fixture(scope="session")
def fake_server() -> Dict[str, str]:
    port = _find_free_port()
    process = multiprocessing.Process(
        target=run_devserver,
        kwargs={"host": "127.0.0.1", "port": port},
        daemon=True,
    )
    process.start()
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_server(base_url + "/")
    except Exception:
        process.terminate()
        process.join(timeout=1)
        raise

    yield {"base_url": base_url, "port": str(port)}

    process.terminate()
    process.join(timeout=2)


@pytest.fixture(autouse=True)
def reset_fake_server(fake_server: Dict[str, str]) -> None:
    _post(f"{fake_server['base_url']}/sei/api/reset")


@pytest.fixture
def fake_settings(monkeypatch: pytest.MonkeyPatch, tmp_path, fake_server: Dict[str, str]) -> Settings:
    monkeypatch.setenv("SEI_USERNAME", "00000000000")
    monkeypatch.setenv("SEI_PASSWORD", "senha_teste")
    monkeypatch.setenv("SEI_BLOCO_ID", "55")
    monkeypatch.setenv("SEI_BASE_URL", "https://example.com/sei/")
    monkeypatch.setenv("SEI_DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setenv("SEI_IS_ADMIN", "true")
    monkeypatch.setenv("SEI_DEV_MODE", "true")
    monkeypatch.setenv("SEI_DEV_BASE_URL", f"{fake_server['base_url']}/sei/")

    settings = Settings.load()
    return settings
