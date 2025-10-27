"""Coleção de tarefas automatizadas do SEIAutomation."""

from .download_zip import download_zip_lote
from .annotate_ok import preencher_anotacoes_ok
from .export_relation import exportar_relacao_csv

__all__ = ["download_zip_lote", "preencher_anotacoes_ok", "exportar_relacao_csv"]
