from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True, frozen=True)
class Settings:
    username: str
    password: str
    bloco_id: int
    base_url: str
    download_dir: Path
    is_admin: bool
    dev_mode: bool
    dev_base_url: str

    @staticmethod
    def load() -> "Settings":
        username = os.getenv("SEI_USERNAME", "").strip()
        password = os.getenv("SEI_PASSWORD", "").strip()

        if not username or not password:
            raise ValueError(
                "Credenciais não encontradas. Defina SEI_USERNAME e SEI_PASSWORD no ambiente ou arquivo .env."
            )

        bloco_id = int(os.getenv("SEI_BLOCO_ID", "55"))
        base_url = os.getenv("SEI_BASE_URL", "https://sei.tjpb.jus.br/sei/").rstrip("/") + "/"
        download_dir = Path(os.getenv("SEI_DOWNLOAD_DIR", "playwright-downloads")).expanduser()
        download_dir.mkdir(parents=True, exist_ok=True)
        is_admin = os.getenv("SEI_IS_ADMIN", "false").strip().lower() in {"1", "true", "yes", "sim"}
        dev_mode = os.getenv("SEI_DEV_MODE", "false").strip().lower() in {"1", "true", "yes", "sim"}
        dev_base_url = os.getenv("SEI_DEV_BASE_URL", "http://127.0.0.1:8001/sei/").strip()
        if dev_base_url:
            dev_base_url = dev_base_url.rstrip("/") + "/"

        return Settings(
            username=username,
            password=password,
            bloco_id=bloco_id,
            base_url=base_url,
            download_dir=download_dir,
            is_admin=is_admin,
            dev_mode=dev_mode,
            dev_base_url=dev_base_url,
        )

    @property
    def target_base_url(self) -> str:
        return self.dev_base_url if self.dev_mode and self.dev_base_url else self.base_url

    def with_dev_mode(self, enabled: bool) -> "Settings":
        if enabled == self.dev_mode:
            return self
        return replace(self, dev_mode=enabled)
