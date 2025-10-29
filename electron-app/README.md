# SEIAutomation Desktop

Aplicativo desktop (Electron + React + TypeScript) que consome a API FastAPI do projeto **SEIAutomation**. Ele permite:

- Autenticar usuários (JWT) e respeitar permissões (admin, auto credentials).
- Selecionar tarefas disponíveis (`download_zip`, `annotate_ok`, `export_relation`).
- Definir parâmetros (ID do bloco, limite, headless, auto credentials, modo desenvolvedor).
- Disparar execuções e acompanhar o log/status das últimas corridas.
- Empacotar binários desktop via `electron-builder`.

## Pré-requisitos

- Node.js 20+
- npm 10+
- Backend SEIAutomation rodando e acessível (por exemplo `http://168.231.97.65:8000`).

## Variáveis de ambiente

Crie um arquivo `.env` (baseado em `.env.example`):

```bash
cp .env.example .env
```

| Variável        | Descrição                                 | Padrão                 |
| --------------- | ----------------------------------------- | ---------------------- |
| `VITE_API_URL`  | URL base da API FastAPI                   | `http://localhost:8000` |

## Scripts principais

Dentro do diretório `seiautomation-electron`:

```bash
npm install                # instala dependências
npm run dev                # inicia Vite + watcher do main + Electron em modo desenvolvimento
npm run build              # gera build do renderer (Vite) e do main/preload (tsc)
npm run package            # gera artefatos via electron-builder (AppImage/Snap por padrão no Linux)
npm run start              # executa o app já compilado (usa dist + dist-electron)
```

> ⚠️ Durante `npm run dev`, o script compila o main uma vez (`npm run build:main`), liga o watcher (`tsc --watch`) e abre o Electron apontando para o dev server (http://localhost:5173). O Electron não reinicia automaticamente quando o `main.ts` muda; basta fechar e executar novamente quando necessário.

## Estrutura do projeto

```
seiautomation-electron/
├─ electron/          # main.ts e preload.ts (processo principal)
├─ src/               # renderer React (contextos, componentes, estilos)
├─ dist/              # saída do renderer (Vite)
├─ dist-electron/     # saída do main/preload compilados (tsc)
├─ build/             # assets para empacotamento (ícones etc.)
└─ package.json       # scripts, dependências e config do electron-builder
```

## Integração com a API

- `POST /auth/login` (form-urlencoded) para obter `access_token`.
- `GET /auth/me` para carregar detalhes do usuário (permissões).
- `GET /tasks/` para listar tarefas disponíveis.
- `POST /tasks/run` para disparar execuções (usa token JWT).
- `GET /tasks/runs` para monitorar histórico/estado.

O token é salvo em `localStorage` e reaplicado automaticamente nos headers `Authorization`. As opções de headless/auto credentials são habilitadas somente se `allow_auto_credentials=true` para o usuário logado.

## Próximos passos sugeridos

- Adicionar WebSocket/SSE para transmissão em tempo real dos logs (substituindo polling a cada 10s).
- Criar fluxo de administração (cadastro/edição de usuários) diretamente no app.
- Personalizar ícones e metadados do `electron-builder` (`build/icon.*`, `description`, `author`).
- Configurar pipeline CI/CD (GitHub Actions) para gerar instaladores automaticamente.
- Avaliar um frontend web (Next.js) reutilizando os componentes React para distribuir no domínio `duds4.com`.

## Fontes / referências

- [Electron](https://www.electronjs.org/)
- [Vite](https://vitejs.dev/)
- [Electron Builder](https://www.electron.build/)
- [Axios](https://axios-http.com/)
