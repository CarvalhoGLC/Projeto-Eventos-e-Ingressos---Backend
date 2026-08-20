# Sistema de Eventos e Ingressos

API back-end para gestão de eventos, venda de ingressos com QR Code
assinado digitalmente, e controle de acesso na portaria.

Construída com **FastAPI**, **SQLAlchemy 2.0** e **SQLite**, com autenticação
via **JWT** e três papéis de usuário distintos: Organizador, Cliente e Portaria.

---

## Índice

- [Funcionalidades](#funcionalidades)
- [Stack técnica](#stack-técnica)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração (.env)](#configuração-env)
- [Rodando o projeto](#rodando-o-projeto)
- [Dados de teste (seed)](#dados-de-teste-seed)
- [Testando via Swagger](#testando-via-swagger)
- [Rotas da API](#rotas-da-api)
- [Rodando os testes automatizados](#rodando-os-testes-automatizados)
- [Rodando com Docker](#rodando-com-docker)
- [Problemas comuns](#problemas-comuns)
- [Notas técnicas e decisões de projeto](#notas-técnicas-e-decisões-de-projeto)

---

## Funcionalidades

- **Autenticação com 3 papéis**: `organizer` (organizador), `client` (cliente)
  e `gate` (portaria), cada um com permissões específicas.
- **Gestão de eventos**: organizadores criam e são donos de seus eventos.
- **Reserva de ingressos**: clientes reservam um assento por evento, com
  garantia de que o mesmo assento nunca é vendido duas vezes.
- **Cobrança simulada**: o pagamento é simulado via flag booleana, sem
  integração com gateway real.
- **QR Code infalsificável**: cada ingresso recebe um payload assinado com
  HMAC-SHA256, impossível de forjar sem o segredo do servidor.
- **Link compartilhável**: cada ingresso tem uma URL pública única para
  consulta, sem precisar de login.
- **Validação na portaria**: valida o QR Code, confere se pertence ao evento
  certo, e impede que o mesmo ingresso seja usado mais de uma vez.
- **Busca externa (TMDb)**: endpoint de exemplo consumindo uma API externa.

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Framework web | FastAPI |
| ORM | SQLAlchemy 2.0 (estilo `Mapped` / `mapped_column`) |
| Banco de dados | SQLite |
| Validação de dados | Pydantic |
| Configuração | pydantic-settings (variáveis de ambiente via `.env`) |
| Autenticação | JWT (`python-jose`) + OAuth2 Password Flow |
| Hash de senha | `passlib` com `bcrypt` |
| Cliente HTTP assíncrono | `httpx` |
| Testes | `pytest` + `TestClient` do FastAPI |

---

## Estrutura do projeto

```
backend/
├── Dockerfile               # imagem de produção (uvicorn, usuário não-root)
├── .dockerignore              # exclui .env, venv, testes etc. da imagem
├── docker-compose.yml           # atalho para build + run com .env e volume
├── requirements.txt                # dependências de produção
├── requirements-dev.txt              # requirements.txt + pytest
└── backend_events_tickets/
    ├── main.py              # cria a app, registra rotas de auth, /me e os routers
    ├── seed.py                # popula organizador, clientes, portaria e um evento de teste
    ├── core/
    │   ├── config.py             # configurações (lê o .env via pydantic-settings)
    │   ├── database.py             # models SQLAlchemy (User, Event, Ticket) e engine
    │   └── auth.py                  # JWT, hash de senha, get_current_user, require_role
    ├── schemas.py                     # schemas Pydantic (UserRegister, EventCreate, BookingRequest)
    ├── services.py                       # busca TMDb, geração/validação do QR Code assinado
    ├── routers/
    │   ├── events.py                        # POST /events
    │   ├── bookings.py                        # POST /bookings, GET /tickets/share/{token}
    │   ├── external.py                          # GET /external/movies
    │   └── gate.py                                # POST /gate/validate
    ├── tests/
    │   ├── conftest.py                              # fixtures: client de teste, banco isolado, login
    │   ├── test_auth.py                               # registro, login e /me
    │   ├── test_events.py                               # criação de evento e permissões
    │   ├── test_bookings.py                               # reserva, assento duplicado, link
    │   ├── test_gate.py                                     # validação, QR forjado, dupla validação
    │   └── test_external.py                                   # busca TMDb (mockada)
    ├── .env                                                      # variáveis reais (não versionado)
    ├── .env.example                                                # modelo do .env, seguro para versionar
    └── tickets_app.db                                                # banco SQLite (gerado automaticamente)
```

---

## Pré-requisitos

- Python 3.11+
- `pip`

---

## Instalação

```bash
# 1. Clone o repositório e entre na pasta backend
cd backend

# 2. Crie e ative um ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic-settings \
    "python-jose[cryptography]" passlib "bcrypt==4.0.1" httpx pytest
```

> ⚠️ **Sobre o `bcrypt==4.0.1`**: versões mais recentes do `bcrypt` removeram
> um atributo interno que o `passlib` usa para checar a versão instalada,
> causando erro `AttributeError: module 'bcrypt' has no attribute '__about__'`.
> Fixar a versão em `4.0.1` evita esse problema.

---

## Configuração (.env)

Crie um arquivo `.env` dentro de `backend_events_tickets/` (ao lado do
`core/config.py`), baseado no `.env.example`:

```env
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=8
TMDB_API_KEY=
QR_SECRET=
```

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave usada para assinar os tokens JWT. **Obrigatória.** |
| `ALGORITHM` | Algoritmo de assinatura do JWT. Padrão: `HS256`. |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Tempo de validade do token de login. Padrão: `8`. |
| `TMDB_API_KEY` | Chave de API do [TMDb](https://www.themoviedb.org/settings/api). **Obrigatória.** |
| `QR_SECRET` | Segredo usado para assinar (HMAC) os QR Codes dos ingressos. **Obrigatória.** |

Gere valores fortes para `SECRET_KEY` e `QR_SECRET` com:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> Se qualquer uma das variáveis obrigatórias estiver faltando, a aplicação
> falha ao iniciar com uma mensagem de erro clara — em vez de rodar
> silenciosamente com valores inválidos.

O caminho do `.env` e do banco `tickets_app.db` são resolvidos de forma
**absoluta**, com base na localização dos arquivos `core/config.py` e
`core/database.py` — então funciona independente de qual pasta você está quando
roda o comando.

---

## Rodando o projeto

De dentro da pasta `backend`:

```bash
fastapi dev backend_events_tickets/main.py
```

O servidor sobe em `http://127.0.0.1:8000`. As tabelas do banco são criadas
automaticamente na primeira execução.

---

## Dados de teste (seed)

Para não precisar cadastrar organizador, clientes e evento na mão toda vez,
o projeto inclui um script de seed. **Rode com o servidor parado**, de
dentro da pasta `backend` (mesma pasta do comando anterior):

```bash
python -m backend_events_tickets.seed
```

É seguro rodar mais de uma vez — ele verifica o que já existe antes de
criar, então não duplica nada. Ao final, ele imprime no terminal as
credenciais e os IDs gerados. Resumo do que fica populado:

| Papel | E-mail | Senha | Observação |
|---|---|---|---|
| Organizador | `organizador@example.com` | `senha123` | dono do evento semeado |
| Cliente 1 | `cliente1@example.com` | `senha123` | já possui o assento `A1` reservado |
| Cliente 2 | `cliente2@example.com` | `senha123` | sem ingresso ainda — pode reservar |
| Portaria | `portaria@example.com` | `senha123` | — |

Mais um evento: **"Show de Lançamento"**, com o assento `A1` já vendido
para o Cliente 1 (ingresso com QR Code assinado e link compartilhável
prontos) e os demais assentos livres para testar uma nova reserva.

---

## Testando via Swagger

Acesse a documentação interativa em:

```
http://127.0.0.1:8000/docs
```

### Roteiro de teste manual (usando os dados semeados)

1. **Rode o seed** (seção anterior), se ainda não rodou.
2. **Clique em "Authorize"** (cadeado no topo da página) → use
   `organizador@example.com` / `senha123` → **Authorize**.
3. **`POST /events`** — crie um novo evento (autenticado como organizador),
   ou use o evento já semeado ("Show de Lançamento") anotando o `id` que o
   script imprimiu.
4. Reautorize com `cliente2@example.com` / `senha123`, e use
   **`POST /bookings`** para reservar um assento livre (`B1`, por exemplo)
   no evento.
5. A resposta traz `qr_code_payload` e `share_link`. Teste
   **`GET /tickets/share/{token}`** com o token do link.
6. Reautorize com `portaria@example.com` / `senha123`, e use
   **`POST /gate/validate`** com o `qr_code_payload` e o `event_id` — tanto
   com o ingresso que você acabou de reservar quanto com o do Cliente 1
   (impresso pelo script de seed) — para liberar a entrada. Chamando de
   novo com o mesmo QR Code retorna `USED`.

---

## Rotas da API

| Método | Rota | Papel exigido | Descrição |
|---|---|---|---|
| `POST` | `/register` | — | Cria um novo usuário |
| `POST` | `/token` | — | Login (OAuth2 Password Flow); retorna o JWT |
| `GET` | `/me` | qualquer autenticado | Retorna os dados do usuário logado (id, email, papel) |
| `GET` | `/external/movies?query=...` | — | Busca filmes no TMDb |
| `POST` | `/events` | `organizer` | Cria um evento |
| `POST` | `/bookings` | `client` | Reserva um assento e gera o ingresso com QR Code |
| `GET` | `/tickets/share/{token}` | — (rota pública) | Consulta um ingresso pelo link compartilhável |
| `POST` | `/gate/validate` | `gate` | Valida um QR Code na entrada do evento |

---

## Rodando os testes automatizados

```bash
pytest backend_events_tickets/tests -v
```

Os testes usam um banco SQLite **isolado** (`tests/test_tickets_app.db`),
criado do zero a cada execução e apagado ao final — não interferem no banco
de desenvolvimento (`tickets_app.db`).

Cobertura da suíte:

- Registro de usuário e bloqueio de e-mail duplicado
- Login com credenciais corretas/incorretas
- Criação de evento restrita a organizadores
- Reserva de ingresso restrita a clientes
- Bloqueio de assento duplicado no mesmo evento
- Bloqueio de reserva quando o pagamento simulado falha
- Consulta de ingresso pelo link compartilhável
- Validação de entrada na portaria
- Bloqueio de reentrada com ingresso já validado
- Rejeição de QR Code adulterado (assinatura inválida)
- Rejeição de ingresso usado no evento errado
- Restrição de acesso à portaria por papel

---

## Rodando com Docker

Como alternativa a instalar Python e as dependências localmente, o projeto
inclui um `Dockerfile`, `.dockerignore`, `docker-compose.yml` e
`requirements.txt` / `requirements-dev.txt` na raiz de `backend/`.

```
backend/
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env
└── backend_events_tickets/
```

### Opção 1 — Docker puro

```bash
docker build -t bilheteria-api .
docker run -p 8000:8000 --env-file backend_events_tickets/.env bilheteria-api
```

### Opção 2 — Docker Compose (recomendado)

Persiste o banco SQLite fora do container, entre rebuilds:

```bash
mkdir -p data && touch data/tickets_app.db
docker compose up --build
```

> O `docker-compose.yml` espera o `.env` na raiz de `backend/`. Se o seu
> `.env` está dentro de `backend_events_tickets/`, copie-o também para a
> raiz, ou ajuste o campo `env_file:` no `docker-compose.yml`.

Em ambos os casos, a API sobe em `http://localhost:8000` e o Swagger em
`http://localhost:8000/docs`, exatamente como no modo local.

### Decisões do Dockerfile

- Roda com **`uvicorn` diretamente** em produção — o `fastapi dev` é só
  para desenvolvimento local, com reload automático.
- Usa um **usuário não-root** (`appuser`) dentro do container, por boa
  prática de segurança.
- **Nenhum segredo vai para dentro da imagem**: o `.env` é ignorado no
  build (via `.dockerignore`) e injetado apenas em tempo de execução, com
  `--env-file` (Docker puro) ou `env_file:` (Compose).
- `bcrypt==4.0.1` continua fixado no `requirements.txt`, pelo mesmo motivo
  de compatibilidade com o `passlib` já explicado na instalação local.

### Rodando os testes dentro do container

O `requirements-dev.txt` não é instalado na imagem de produção. Para rodar a
suíte de testes dentro do container, monte a pasta do projeto e instale as
dependências de teste na hora:

```bash
docker run --rm \
    -v "$(pwd)":/app \
    --env-file backend_events_tickets/.env \
    bilheteria-api \
    sh -c "pip install -r requirements-dev.txt && pytest backend_events_tickets/tests -v"
```

(No Windows PowerShell, troque `"$(pwd)"` por `${PWD}`.)

---

## Problemas comuns

Erros que apareceram durante o desenvolvimento deste projeto e como
resolvê-los, caso você bata neles ao configurar o ambiente:

### `ModuleNotFoundError: No module named 'backend_events_tickets'`

Falta um `__init__.py` em alguma pasta do pacote. Confirme que existem
(vazios) em: `backend_events_tickets/__init__.py`,
`backend_events_tickets/core/__init__.py`,
`backend_events_tickets/routers/__init__.py` e
`backend_events_tickets/tests/__init__.py`. Se rodou os testes com o
comando `pytest` puro e mesmo assim deu esse erro, tente
`python -m pytest backend_events_tickets/tests -v` de dentro de `backend/`
— o `-m` garante que o diretório atual entra no `sys.path`.

### `AttributeError: module 'bcrypt' has no attribute '__about__'`

Incompatibilidade entre `passlib` e versões recentes do `bcrypt` (4.1+).
Corrija fixando a versão:

```bash
pip install "bcrypt==4.0.1"
```

### `Import error: N validation errors for Settings ... Field required`

O `Settings` (`core/config.py`) não encontrou o `.env`, ou não achou uma
das variáveis obrigatórias (`SECRET_KEY`, `TMDB_API_KEY`, `QR_SECRET`).
Confirme que o `.env` existe em `backend_events_tickets/.env` (não dentro
de `core/`) e tem as três chaves preenchidas. Esse caminho é calculado
automaticamente em `core/config.py` a partir de
`Path(__file__).resolve().parent.parent` — se você mover `config.py` de
lugar, esse cálculo precisa ser ajustado junto.

### Front-end não consegue chamar a API (erro de CORS no navegador)

O `main.py` já libera `allow_origins=["*"]` via `CORSMiddleware`. Se ainda
assim der erro de CORS, confirme que o back-end está rodando e que a URL
em `VITE_API_BASE_URL` (front-end) aponta para o endereço certo.

### Reorganizei os arquivos e a aplicação parou de achar o `.env`/banco

Tanto `core/config.py` quanto `core/database.py` calculam o caminho do
`.env`/`tickets_app.db` subindo **dois** níveis a partir de si mesmos
(`core/` → `backend_events_tickets/`). Se algum desses arquivos for movido
para outro nível de pasta, o cálculo (`parent.parent`) precisa acompanhar.

---

## Notas técnicas e decisões de projeto

- **Modelos SQLAlchemy 2.0**: usam `Mapped`/`mapped_column` em vez do estilo
  legado `Column()`, o que dá tipagem correta para ferramentas como Pylance.
- **`Event.organizer_id` é obrigatório** — todo evento precisa ter um
  organizador; não é permitido criar evento órfão.
- **`Ticket` acumula o papel de reserva + ingresso** em uma única tabela
  (não existe uma entidade "Booking" separada).
- **`QR_SECRET` e `TMDB_API_KEY` não ficam hardcoded no código** — ambos
  vêm do `.env`, junto com o `SECRET_KEY` do JWT.
- **`GET /tickets/share/{token}` é uma rota pública** (sem autenticação),
  propositalmente, para permitir o compartilhamento do ingresso.
- **Cobrança 100% simulada** — não há integração com gateway de pagamento
  real; o campo `simulate_payment_success` decide se a reserva é aceita.