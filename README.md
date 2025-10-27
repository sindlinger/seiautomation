# SEIAutomation

Automação das tarefas repetitivas no SEI/TJPB. O projeto fornece:

1. **Scripts reutilizáveis**
   - Download dos processos do bloco interno configurado (ex.: *Peritos – bloco 55*) em formato ZIP.
   - Preenchimento automático do campo "Anotações" com o texto **OK** nos processos que ainda não possuem esse status.

2. **Aplicativo com interface (PySide6)**
   - Ícone na bandeja do sistema.
   - Janela simples com checkboxes para escolher quais tarefas executar e se o navegador roda em modo headless.

Compatível com Windows e WSL (necessário Python 3.10+).

---

## Instalação

1. **Criar e ativar um ambiente virtual (recomendado)**

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/WSL
.venv\Scripts\activate           # Windows
```

2. **Instalar dependências**

```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Configurar variáveis**

Copie `.env.example` para `.env` e informe usuário/senha:

```
SEI_USERNAME=00000000000
SEI_PASSWORD=sua_senha
SEI_BLOCO_ID=55
SEI_DOWNLOAD_DIR=playwright-downloads
SEI_BASE_URL=https://sei.tjpb.jus.br/sei/
SEI_IS_ADMIN=false
SEI_DEV_MODE=false
SEI_DEV_BASE_URL=http://127.0.0.1:8001/sei/
```

---

## Uso dos scripts

Você pode chamar as funções diretamente em Python:

```python
from seiautomation.config import Settings
from seiautomation.tasks import download_zip_lote, preencher_anotacoes_ok

settings = Settings.load()

# Baixa todos os ZIPs (ignora os que já existem)
download_zip_lote(settings, headless=True, bloco_id=55)

# Preenche anotações com "OK"
preencher_anotacoes_ok(settings, headless=False, bloco_id=55)

# Exporta a lista do bloco para CSV
from seiautomation.tasks import exportar_relacao_csv
exportar_relacao_csv(settings, bloco_id=55)
```

`headless=True` executa sem abrir a janela do navegador. Há também o parâmetro `auto_credentials` para desabilitar o preenchimento automático de login (a interface só habilita essa opção para administradores – `SEI_IS_ADMIN=true`).

---

## Aplicativo gráfico

Para abrir a interface (com bandeja do sistema):

```bash
python main.py
```

Informe o ID do bloco (padrão: valor de `SEI_BLOCO_ID`), marque as tarefas desejadas — baixar ZIPs, preencher "OK" ou exportar a relação — escolha se o navegador deve ser headless e clique em **Executar**. Logs aparecem em tempo real. A janela pode ser minimizada para o tray.

### Modo desenvolvedor (servidor fake)

Para testar os scripts sem acessar o SEI real:

1. Inicie o servidor fake:

   ```bash
   python -m seiautomation.devserver.app  # escuta em http://127.0.0.1:8001
   ```

2. Ative o modo desenvolvedor:
   - Via `.env`: defina `SEI_DEV_MODE=true` (o endereço padrão é `http://127.0.0.1:8001/sei/`, mas pode ser alterado em `SEI_DEV_BASE_URL`).
   - Ou na interface gráfica marque o checkbox **Modo desenvolvedor (usar servidor fake)** antes de executar as tarefas.

   Os scripts abrirão a página simulada e executarão todo o fluxo (downloads, anotações, exportação) contra os elementos fake, permitindo validação local.

---

## Gerar executável (opcional)

Requer [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile main.py
```

O executável ficará em `dist/main.exe`.

---

## Integração com automações futuras

Os módulos estão organizados para permitir inclusão de novas tarefas. Cada rotina deve receber um objeto `Settings` e uma função de `progress` opcional, garantindo que possam ser reutilizadas tanto pelos scripts quanto pela GUI ou qualquer outro orquestrador (por exemplo, chamadas via Docker/MCP/Codex CLI).

---

## Backend API (FastAPI)

O diretório `backend/app` contém uma API que expõe autenticação, catálogo de tarefas e execução assíncrona.

### Instalação

```bash
pip install -r requirements.txt
playwright install chromium      # necessário para as tarefas reutilizadas
```

Defina no `.env` os valores:

```
APP_DATABASE_URL=sqlite:///./seiautomation.db
APP_JWT_SECRET=troque_esta_chave
APP_JWT_EXPIRES_MINUTES=120
```

Crie o primeiro administrador:

```bash
python -m backend.app.manage create-admin --email admin@exemplo.com
```

### Execução

```bash
uvicorn backend.app.main:app --reload
```

Rotas principais:

- `POST /auth/login` – retorna JWT.
- `GET /tasks/` – lista tarefas disponíveis.
- `POST /tasks/run` – dispara uma execução (necessita token). Payload exemplo:

  ```json
  {
    "task_slug": "download_zip",
    "headless": true,
    "auto_credentials": true,
    "limit": null,
    "bloco_id": 55
  }
  ```
- `GET /tasks/runs` – histórico do usuário (ou de todos, se admin).
- `GET /tasks/runs` – histórico do usuário (ou de todos, se admin).

As execuções reutilizam `seiautomation.tasks` e respeitam as permissões `allow_auto_credentials` dos usuários.
