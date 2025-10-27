from __future__ import annotations

import csv
from pathlib import Path

from seiautomation.tasks import download_zip_lote, exportar_relacao_csv, preencher_anotacoes_ok


def test_tasks_against_fake_server(fake_settings) -> None:
    settings = fake_settings.with_dev_mode(True)

    arquivos = list(
        download_zip_lote(
            settings,
            headless=True,
            auto_credentials=True,
            bloco_id=55,
        )
    )
    assert arquivos, "Nenhum arquivo ZIP foi gerado."
    for nome in arquivos:
        caminho = settings.download_dir / nome
        assert caminho.exists(), f"Arquivo esperado não encontrado: {caminho}"
        assert caminho.suffix == ".zip"

    atualizados = preencher_anotacoes_ok(
        settings,
        headless=True,
        auto_credentials=True,
        bloco_id=55,
    )
    assert atualizados == 1

    csv_path = exportar_relacao_csv(
        settings,
        headless=True,
        bloco_id=55,
    )
    assert csv_path.exists()

    with csv_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    assert len(rows) == 2
    assert all(row["anotacoes"] == "OK" for row in rows)
