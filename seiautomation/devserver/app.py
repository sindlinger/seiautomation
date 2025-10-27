from __future__ import annotations

import copy
import io
import json
from typing import Dict, List
from zipfile import ZipFile

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse


ANNOTATION_ICON = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'>"
    "<rect width='24' height='24' rx='3' fill='%23fdd835' stroke='%23f57f17' stroke-width='1'/>"
    "<text x='12' y='17' font-size='14' text-anchor='middle' fill='%23d32f2f'>!</text>"
    "</svg>"
)

ZIP_ICON = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'>"
    "<rect x='4' y='4' width='24' height='24' rx='4' fill='%232196f3'/>"
    "<text x='16' y='22' font-size='14' text-anchor='middle' fill='white'>ZIP</text>"
    "</svg>"
)


DEFAULT_BLOCKS = {
    55: {
        "name": "Peritos",
        "processes": [
            {"numero": "0800001-23.2024.8.15.0001", "tipo": "Procedimento", "anotacao": ""},
            {"numero": "0800002-11.2024.8.15.0001", "tipo": "Procedimento", "anotacao": "OK"},
        ],
    },
    77: {
        "name": "Exemplo",
        "processes": [
            {"numero": "0800003-55.2024.8.15.0001", "tipo": "Processo", "anotacao": ""},
        ],
    },
}

BLOCKS = copy.deepcopy(DEFAULT_BLOCKS)


def reset_state() -> None:
    global BLOCKS
    BLOCKS = copy.deepcopy(DEFAULT_BLOCKS)

def _render_login_page() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>SEI (Fake) - Login</title>
</head>
<body>
  <h1>SEI Fake - Login</h1>
  <form id="login-form">
    <label>Usuário <input id="txtUsuario" name="usuario" /></label><br/>
    <label>Senha <input id="pwdSenha" type="password" name="senha" /></label><br/>
    <button type="submit">Acessar</button>
  </form>
  <script>
    document.getElementById("login-form").addEventListener("submit", function (event) {
      event.preventDefault();
      window.location.href = "/sei/home?infra_unidade_atual=110001126";
    });
  </script>
</body>
</html>
"""


def _render_home_page() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>SEI (Fake) - Home</title>
</head>
<body>
  <h1>SEI Fake - Home</h1>
  <nav>
    <a href="#" id="menu-blocos">Blocos</a>
    <a href="/sei/controlador.php?acao=bloco_interno_listar" id="menu-internos">Internos</a>
  </nav>
  <script>
    document.getElementById("menu-blocos").addEventListener("click", function (event) {
      event.preventDefault();
    });
  </script>
</body>
</html>
"""


def _render_blocks_page(blocks: Dict[int, Dict]) -> str:
    rows = "\n".join(
        f"""
      <tr>
        <td>{idx}</td>
        <td><a href="/sei/controlador.php?acao=rel_bloco_protocolo_listar&id_bloco={idx}&infra_hash=fakehash">{idx}</a></td>
        <td>{data['name']}</td>
      </tr>
    """
        for idx, data in blocks.items()
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>SEI (Fake) - Blocos internos</title>
</head>
<body>
  <h1>Blocos internos</h1>
  <table border="1" id="tabela-blocos">
    <tr><th>#</th><th>ID</th><th>Nome</th></tr>
    {rows}
  </table>
</body>
</html>
"""


def _render_process_table(block_id: int, processes: List[Dict[str, str]]) -> str:
    processes_json = json.dumps(processes)
    rows = []
    for idx, process in enumerate(processes, start=1):
        numero = process["numero"]
        anot = process.get("anotacao", "")
        rows.append(
            f"""
      <tr data-numero="{numero}">
        <td><input type="checkbox" /></td>
        <td>{idx}</td>
        <td><a target="_blank" href="/sei/processo/{numero}?numero={numero}">{numero}</a></td>
        <td>{process['tipo']}</td>
        <td class="anotacao" data-numero="{numero}">{anot}</td>
        <td>
            <img src="{ANNOTATION_ICON}" width="24" height="24" title="Anotações" data-numero="{numero}" class="acao-anotacao" />
        </td>
      </tr>
    """
        )

    rows_html = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Bloco {block_id} - Relação</title>
</head>
<body>
  <h1>Bloco {block_id}</h1>
  <table border="1" id="tabela-processos">
    <tr><th></th><th>Seq</th><th>Número</th><th>Tipo</th><th>Anotações</th><th>Ações</th></tr>
    {rows_html}
  </table>
  <script>
    window.__fakeSeiState = {{
      blocoId: {block_id},
      processos: {processes_json}
    }};

    function abrirModal(numero) {{
      const iframe = document.createElement("iframe");
      iframe.name = "modal-frame";
      iframe.src = "/sei/modal/anotacao?numero=" + encodeURIComponent(numero);
      iframe.style.width = "400px";
      iframe.style.height = "200px";
      iframe.style.border = "1px solid #444";
      document.body.appendChild(iframe);
    }}

    window.fecharModal = function () {{
      const frame = document.querySelector("iframe[name='modal-frame']");
      if (frame) frame.remove();
    }};

    window.salvarAnotacao = function (numero, valor) {{
      const alvo = document.querySelector("td.anotacao[data-numero='" + numero + "']");
      if (alvo) {{
        alvo.textContent = valor;
      }}
      window.__fakeSeiState.processos = window.__fakeSeiState.processos.map(function (proc) {{
        if (proc.numero === numero) {{
          return Object.assign({{}}, proc, {{anotacao: valor}});
        }}
        return proc;
      }});
      fetch("/sei/api/anotacao", {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json"
        }},
        body: JSON.stringify({{ bloco_id: window.__fakeSeiState.blocoId, numero: numero, valor: valor }})
      }}).catch(function () {{ /* ignora erros no modo fake */ }});
      window.fecharModal();
    }};

    document.querySelectorAll("img.acao-anotacao").forEach(function (img) {{
      img.addEventListener("click", function (event) {{
        const numero = event.currentTarget.dataset.numero;
        abrirModal(numero);
      }});
    }});
  </script>
</body>
</html>
"""


def _render_annotation_modal(numero: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Anotações - {numero}</title>
</head>
<body>
  <h2>Anotações para {numero}</h2>
  <form id="form-anotacao">
    <label>Texto: <input id="txtAnotacao" name="txtAnotacao" /></label>
    <button type="submit" name="sbmAlterarRelBlocoProtocolo">Salvar</button>
  </form>
  <script>
    const numero = {numero!r};
    window.addEventListener("load", function () {{
      const atual = parent.window.__fakeSeiState.processos.find(function (proc) {{
        return proc.numero === numero;
      }});
      if (atual && atual.anotacao) {{
        document.getElementById("txtAnotacao").value = atual.anotacao;
      }}
    }});

    document.getElementById("form-anotacao").addEventListener("submit", function (event) {{
      event.preventDefault();
      const valor = document.getElementById("txtAnotacao").value || "";
      if (parent && parent.salvarAnotacao) {{
        parent.salvarAnotacao(numero, valor);
      }}
    }});
  </script>
</body>
</html>
"""


def _render_process_popup(numero: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Processo {numero}</title>
</head>
<body>
  <iframe name="ifrConteudoVisualizacao" src="/sei/processo/{numero}/conteudo" width="800" height="400"></iframe>
  <script>
    window.abrirZipFrame = function () {{
      if (document.querySelector("iframe[name='ifrVisualizacao']")) {{
        return;
      }}
      const iframe = document.createElement("iframe");
      iframe.name = "ifrVisualizacao";
      iframe.src = "/sei/processo/{numero}/zip";
      iframe.width = "600";
      iframe.height = "200";
      document.body.appendChild(iframe);
    }};
  </script>
</body>
</html>
"""


def _render_process_content(numero: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8" /></head>
<body>
  <p>Processo {numero}</p>
  <img src="{ZIP_ICON}" width="32" height="32" title="Gerar Arquivo ZIP do Processo" onclick="parent.abrirZipFrame()" style="cursor:pointer;" />
</body>
</html>
"""


def _render_zip_frame(numero: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8" /></head>
</head>
<body>
  <form>
    <label><input type="radio" name="tipo" value="todos" checked /> Todos os documentos disponíveis</label>
  </form>
  <button id="btn-gerar">Gerar</button>
  <a id="link-download" href="/sei/download/{numero}.zip" download style="display:none;">Gerar</a>
  <script>
    document.getElementById("btn-gerar").addEventListener("click", function (event) {{
      event.preventDefault();
      document.getElementById("link-download").click();
    }});
  </script>
</body>
</html>
"""


def create_app() -> FastAPI:
    app = FastAPI(title="SEI Fake Server", description="Servidor fake para testes do SEIAutomation.")

    @app.get("/sei/controlador.php")
    async def controlador(request: Request) -> Response:
        acao = request.query_params.get("acao")
        if acao == "procedimento_controlar":
            return HTMLResponse(_render_login_page())
        if acao == "bloco_interno_listar":
            return HTMLResponse(_render_blocks_page(BLOCKS))
        if acao == "rel_bloco_protocolo_listar":
            bloco_id = int(request.query_params.get("id_bloco", "55"))
            bloco = BLOCKS.get(bloco_id)
            if not bloco:
                raise HTTPException(status_code=404, detail="Bloco não encontrado.")
            return HTMLResponse(_render_process_table(bloco_id, bloco["processes"]))

        return HTMLResponse("<p>Ação não suportada.</p>", status_code=400)

    @app.get("/sei/home")
    async def home() -> Response:
        return HTMLResponse(_render_home_page())

    @app.get("/sei/modal/anotacao")
    async def modal_anotacao(numero: str) -> Response:
        return HTMLResponse(_render_annotation_modal(numero))

    @app.get("/sei/processo/{numero}")
    async def processo(numero: str) -> Response:
        return HTMLResponse(_render_process_popup(numero))

    @app.get("/sei/processo/{numero}/conteudo")
    async def processo_conteudo(numero: str) -> Response:
        return HTMLResponse(_render_process_content(numero))

    @app.get("/sei/processo/{numero}/zip")
    async def processo_zip(numero: str) -> Response:
        return HTMLResponse(_render_zip_frame(numero))

    @app.get("/sei/download/{numero}.zip")
    async def download(numero: str) -> Response:
        buffer = io.BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr("README.txt", f"Arquivo fake do processo {numero}\n")
        buffer.seek(0)
        headers = {"Content-Disposition": f'attachment; filename="processo_{numero}.zip"'}
        return StreamingResponse(buffer, media_type="application/zip", headers=headers)

    @app.post("/sei/api/anotacao")
    async def atualizar_anotacao(request: Request) -> Response:
        payload = await request.json()
        bloco_id = int(payload.get("bloco_id", 55))
        numero = payload.get("numero")
        valor = payload.get("valor", "")
        bloco = BLOCKS.get(bloco_id)
        if not bloco:
            raise HTTPException(status_code=404, detail="Bloco não encontrado.")
        for processo in bloco["processes"]:
            if processo["numero"] == numero:
                processo["anotacao"] = valor
                break
        return Response(status_code=204)

    @app.post("/sei/api/reset")
    async def reset_endpoint() -> Response:
        reset_state()
        return Response(status_code=204)

    @app.get("/")
    async def root() -> Response:
        return RedirectResponse(url="/sei/controlador.php?acao=procedimento_controlar&id_procedimento=0")

    return app


def run_devserver(host: str = "127.0.0.1", port: int = 8001) -> None:
    import uvicorn

    uvicorn.run("seiautomation.devserver.app:create_app", host=host, port=port, factory=True, reload=False)


if __name__ == "__main__":
    run_devserver()
