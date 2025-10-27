from __future__ import annotations

import os
from dataclasses import dataclass
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

        return Settings(
            username=username,
            password=password,
            bloco_id=bloco_id,
            base_url=base_url,
            download_dir=download_dir,
            is_admin=is_admin,
        )
