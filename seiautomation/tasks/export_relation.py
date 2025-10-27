from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from ..browser import launch_session
from ..config import Settings
from ..navigation import iterar_paginas, login_and_open_bloco

ProgressFn = Callable[[str], None] | None


def _log(message: str, progress: ProgressFn) -> None:
    if progress:
        progress(message)
    else:
        print(message)


def exportar_relacao_csv(
    settings: Settings,
    *,
    headless: bool = True,
    progress: ProgressFn = None,
    bloco_id: int | None = None,
    auto_credentials: bool = True,
) -> Path:
    """
    Exporta a relação do bloco para um arquivo CSV.

    Returns:
        Caminho do arquivo CSV gerado.
    """
    target_bloco = bloco_id or settings.bloco_id
    download_dir = settings.download_dir
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = download_dir / f"bloco_{target_bloco}_relacao_{timestamp}.csv"

    with launch_session(headless=headless) as session:
        page = session.page
        login_and_open_bloco(
            page,
            settings,
            bloco_id=target_bloco,
            progress=progress,
            auto_credentials=auto_credentials,
        )

        rows_data: list[dict[str, str]] = []
        for row, numero in iterar_paginas(page, progress=progress):
            seq = row.locator("td").nth(1).inner_text(timeout=5000).strip()
            tipo = row.locator("td").nth(3).inner_text(timeout=5000).strip()
            anotacao = row.locator("td").nth(4).inner_text(timeout=5000).strip()
            rows_data.append(
                {
                    "sequencia": seq,
                    "processo": numero,
                    "tipo": tipo,
                    "anotacoes": anotacao,
                }
            )

    with filename.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["sequencia", "processo", "tipo", "anotacoes"])
        writer.writeheader()
        writer.writerows(rows_data)

    _log(f"Relação exportada para {filename}", progress)
    return filename
