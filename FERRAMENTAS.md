# Ferramentas e bibliotecas utilizadas

## FastAPI
Framework web assíncrono para Python que facilita criar APIs com validação automática, documentação Swagger e alto desempenho.

## Uvicorn
Servidor ASGI (Asynchronous Server Gateway Interface) leve e rápido, responsável por executar a aplicação FastAPI e aceitar conexões HTTP.

## SQLAlchemy
ORM (Object Relational Mapper) e toolkit SQL que simplifica a interação com bancos de dados relacionais usando objetos Python.

## python-dotenv
Carrega variáveis definidas em arquivos `.env` para o ambiente, permitindo configurar credenciais ou URLs sem hardcode no código.

## passlib[bcrypt]
Biblioteca para hashing de senhas. O extra `bcrypt` habilita o algoritmo bcrypt, padrão robusto para armazenar senhas com segurança.

## python-jose[cryptography]
Implementa operações relacionadas a JSON Web Tokens (JWT) e criptografia. Usado para gerar e validar tokens de autenticação.

## pydantic[email]
Usada pelo FastAPI para validação de dados e criação de modelos tipo-safe. O extra `email` adiciona validações específicas de e-mail.

## Playwright
Framework de automação de navegadores (Chromium, Firefox, WebKit) com suporte a scripts headless. Utilizado para interagir com o SEI automaticamente.

## uv
Gerenciador de ambientes e dependências Python de alta performance. Substitui pip/venv tradicionais com comandos simples (`uv pip`, `uv run`), mantendo caches otimizados.

## Nginx
Servidor web/proxy reverso. Recebe as requisições em `duds.ws` e repassa internamente para o Uvicorn (porta 8000). Também serve arquivos estáticos e gerencia SSL.

## Certbot
Ferramenta da EFF para emitir e renovar certificados SSL/TLS gratuitos via Let's Encrypt. Integra-se com o Nginx para ativar HTTPS.

## systemd
Gerenciador de serviços do Linux. Mantém o processo do Uvicorn rodando em background, reinicia em caso de falhas e inicializa o backend no boot.

## Electron
Plataforma para construir aplicações desktop com tecnologias web (HTML, CSS, JS). Empacota o frontend React para Windows/macOS/Linux consumindo a API.

