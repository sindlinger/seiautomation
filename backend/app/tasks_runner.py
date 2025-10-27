from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Dict, Iterable

from seiautomation.config import Settings as AutomationSettings
from seiautomation.tasks import download_zip_lote, preencher_anotacoes_ok, exportar_relacao_csv

from .models import User
from .schemas import TaskDefinition, TaskRunCreate


@dataclass(slots=True, frozen=True)
class RegisteredTask:
    slug: str
    name: str
    description: str
    handler: Callable[[AutomationSettings, TaskRunCreate, User, Callable[[str], None]], None]


def _download_handler(
    settings: AutomationSettings,
    request: TaskRunCreate,
    user: User,
    progress: Callable[[str], None],
) -> None:
    download_zip_lote(
        settings,
        headless=request.headless,
        progress=progress,
        skip_existentes=True,
        limite=request.limit,
        auto_credentials=request.auto_credentials,
        bloco_id=request.bloco_id,
    )


def _annotate_handler(
    settings: AutomationSettings,
    request: TaskRunCreate,
    user: User,
    progress: Callable[[str], None],
) -> None:
    preencher_anotacoes_ok(
        settings,
        headless=request.headless,
        progress=progress,
        auto_credentials=request.auto_credentials,
        bloco_id=request.bloco_id,
    )


def _export_handler(
    settings: AutomationSettings,
    request: TaskRunCreate,
    user: User,
    progress: Callable[[str], None],
) -> None:
    exportar_relacao_csv(
        settings,
        headless=request.headless,
        progress=progress,
        bloco_id=request.bloco_id,
        auto_credentials=request.auto_credentials,
    )


TASKS: Dict[str, RegisteredTask] = {
    "download_zip": RegisteredTask(
        slug="download_zip",
        name="Download de ZIPs",
        description="Baixa todos os processos do bloco configurado em formato ZIP.",
        handler=_download_handler,
    ),
    "annotate_ok": RegisteredTask(
        slug="annotate_ok",
        name="Atualizar anotações",
        description='Preenche o campo "Anotações" com o texto OK para os processos do bloco.',
        handler=_annotate_handler,
    ),
    "export_relation": RegisteredTask(
        slug="export_relation",
        name="Exportar relação",
        description="Exporta a lista de processos do bloco para CSV.",
        handler=_export_handler,
    ),
}


def list_tasks() -> Iterable[TaskDefinition]:
    for task in TASKS.values():
        yield TaskDefinition(name=task.name, slug=task.slug, description=task.description)


def execute_task(
    task_request: TaskRunCreate,
    user: User,
    progress: Callable[[str], None],
) -> None:
    task = TASKS.get(task_request.task_slug)
    if not task:
        raise ValueError("Tarefa desconhecida.")

    auto_credentials = task_request.auto_credentials and user.allow_auto_credentials
    if task_request.auto_credentials and not user.allow_auto_credentials:
        progress("Aviso: usuário não tem permissão para auto-preenchimento. Continuando em modo manual.")

    automation_settings = AutomationSettings.load()
    if task_request.dev_mode is not None:
        automation_settings = automation_settings.with_dev_mode(task_request.dev_mode)
    if task_request.bloco_id:
        automation_settings = replace(automation_settings, bloco_id=task_request.bloco_id)

    request_payload = task_request.model_copy(
        update={
            "auto_credentials": auto_credentials,
            "dev_mode": automation_settings.dev_mode,
        }
    )

    task.handler(
        automation_settings,
        request_payload,
        user,
        progress,
    )
