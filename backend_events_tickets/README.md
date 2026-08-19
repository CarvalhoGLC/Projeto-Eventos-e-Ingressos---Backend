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
- [Testando via Swagger](#testando-via-swagger)
- [Rotas da API](#rotas-da-api)
- [Rodando os testes automatizados](#rodando-os-testes-automatizados)
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
└── backend_events_tickets/
    ├── main.py              # cria a app, registra rotas de auth e os routers
    ├── config.py             # configurações (lê o .env via pydantic-settings)
    ├── database.py             # models SQLAlchemy (User, Event, Ticket) e engine
    ├── schemas.py                # schemas Pydantic (UserRegister, EventCreate, BookingRequest)
    ├── auth.py                     # JWT, hash de senha, get_current_user, require_role
    ├── services.py                   # busca TMDb, geração/validação do QR Code assinado
    ├── routers/
    │   ├── events.py                   # POST /events
    │   ├── bookings.py                   # POST /bookings, GET /tickets/share/{token}
    │   ├── external.py                     # GET /external/movies
    │   └── gate.py                           # POST /gate/validate
    ├── tests/
    │   ├── conftest.py                         # fixtures: client de teste, banco isolado, login
    │   ├── test_auth.py                          # registro e login
    │   ├── test_events.py                          # criação de evento e permissões
    │   ├── test_bookings.py                          # reserva, assento duplicado, link
    │   ├── test_gate.py                                # validação, QR forjado, dupla validação
    │   └── test_external.py                             # busca TMDb (mockada)
    ├── .env                                                # variáveis reais (não versionado)
    ├── .env.example                                          # modelo do .env, seguro para versionar
    └── tickets_app.db                                          # banco SQLite (gerado automaticamente)
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
`config.py`), baseado no `.env.example`:

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
**absoluta**, com base na localização dos arquivos `config.py` e
`database.py` — então funciona independente de qual pasta você está quando
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

## Testando via Swagger

Acesse a documentação interativa em:

```
http://127.0.0.1:8000/docs
```

### Roteiro de teste manual

1. **`POST /register`** — crie um usuário organizador:
   ```json
   {"email": "organizador@exemplo.com", "password": "senha123", "role": "organizer"}
   ```
2. **Clique em "Authorize"** (cadeado no topo da página) → informe o
   `username` (email) e `password` cadastrados → **Authorize**. O Swagger
   faz login e usa o token automaticamente nas próximas chamadas.
3. **`POST /events`** — crie um evento (autenticado como organizador).
4. Registre um segundo usuário com `role: "client"`, reautorize com ele, e
   use **`POST /bookings`** para reservar um assento no evento criado.
5. A resposta traz `qr_code_payload` e `share_link`. Teste
   **`GET /tickets/share/{token}`** com o token do link.
6. Registre um terceiro usuário com `role: "gate"`, reautorize, e use
   **`POST /gate/validate`** com o `qr_code_payload` e o `event_id` para
   liberar a entrada. Chamando de novo com o mesmo QR Code retorna `USED`.

---

## Rotas da API

| Método | Rota | Papel exigido | Descrição |
|---|---|---|---|
| `POST` | `/register` | — | Cria um novo usuário |
| `POST` | `/token` | — | Login (OAuth2 Password Flow); retorna o JWT |
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