from __future__ import annotations

import time
from typing import Callable, Tuple

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .config import Settings


def _log(message: str, progress: Callable[[str], None] | None) -> None:
    if progress:
        progress(message)
    else:
        print(message)


def _select_active_page(page: Page, base_host: str) -> Tuple[Page, bool]:
    context = page.context
    pages = [p for p in context.pages if not p.is_closed()]
    for candidate in pages[::-1]:  # check newest first
        url = candidate.url or ""
        if base_host in url:
            return candidate, candidate is not page
    return page, False


def login_and_open_bloco(
    page: Page,
    settings: Settings,
    bloco_id: int,
    *,
    progress: Callable[[str], None] | None = None,
    auto_credentials: bool = True,
) -> None:
    base = settings.target_base_url
    login_url = f"{base}controlador.php?acao=procedimento_controlar&id_procedimento=0"
    base_host = settings.target_base_url.split("//", 1)[-1].split("/", 1)[0]
    _log("Acessando página de login…", progress)
    page.goto(login_url, wait_until="domcontentloaded")
    if auto_credentials:
        _log("Efetuando login automático…", progress)
        page.fill("#txtUsuario", settings.username)
        page.fill("#pwdSenha", settings.password)
        page.locator("button:has-text('Acessar')").click()
    else:
        _log("Aguardando login manual do usuário…", progress)

    wait_timeout = 120000 if not auto_credentials else 30000

    if not auto_credentials:
        deadline = time.time() + wait_timeout / 1000
        active_page = page
        manual_detected = False
        while time.time() < deadline:
            active_page, switched = _select_active_page(active_page, base_host)
            if switched:
                page = active_page
            url = active_page.url or ""
            if "infra_unidade_atual" in url:
                manual_detected = True
                break
            time.sleep(0.3)
        if not manual_detected:
            raise PlaywrightTimeoutError("Timeout aguardando conclusão do login manual.")
    else:
        try:
            page.wait_for_url("**infra_unidade_atual**", timeout=wait_timeout, wait_until="domcontentloaded")
        except PlaywrightTimeoutError as exc:
            if "infra_unidade_atual" not in page.url:
                raise exc
            _log(
                "Aviso: tempo limite atingido aguardando o carregamento completo pós-login, prosseguindo assim mesmo.",
                progress,
            )

    if page.is_closed():
        page, _ = _select_active_page(page, base_host)

    page.bring_to_front()

    _log("Abrindo menu Blocos › Internos…", progress)
    page.locator("a:has-text('Blocos')").first.click()
    page.wait_for_timeout(300)
    page.locator("a:has-text('Internos')").first.click()
    page.wait_for_url("**acao=bloco_interno_listar**")

    bloco_link = page.locator("tr", has_text=str(bloco_id)).locator("a", has_text=str(bloco_id)).first
    if bloco_link.count() == 0:
        raise RuntimeError(f"Bloco {bloco_id} não encontrado na lista.")

    _log(f"Abrindo bloco {bloco_id}…", progress)
    bloco_link.click()
    page.wait_for_url(f"**id_bloco={bloco_id}**")
    page.wait_for_selector("table tr:nth-child(2)")


def iterar_paginas(page: Page, progress: Callable[[str], None] | None = None):
    visited_numbers: set[str] = set()
    page_index = 1
    while True:
        _log(f"Processando página {page_index}…", progress)
        rows = page.locator("table tr")
        row_count = rows.count()
        if row_count <= 1:
            break

        page_has_new = False
        for idx in range(1, row_count):
            row = rows.nth(idx)
            numero = row.locator("td").nth(2).inner_text(timeout=5000).strip()
            if not numero or numero in visited_numbers:
                continue
            visited_numbers.add(numero)
            page_has_new = True
            yield row, numero

        # identifica botão próxima página
        next_button = page.locator("a[title*='Próxima'], a:has-text('Próxima'), a:has-text('Próximo')").filter(
            has_text="Próxima"
        )
        if next_button.count() == 0:
            break
        classes = next_button.first.get_attribute("class") or ""
        if "Des" in classes or "disabled" in classes.lower():
            break
        try:
            next_button.first.click()
            page.wait_for_timeout(1200)
            page_index += 1
        except Exception:
            break

        if not page_has_new:
            break
