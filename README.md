# FastAPI do Zero — API de tarefas

[![pipeline](https://github.com/Lucasrlcaldeira/fastapi_zero/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Lucasrlcaldeira/fastapi_zero/actions/workflows/pipeline.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791)

API REST de **lista de tarefas (to-do)** com cadastro de usuários e
autenticação via **JWT**, construída durante o curso
[FastAPI do Zero](https://fastapidozero.dunossauro.com/), do Dunossauro.

🔗 **Documentação interativa (Swagger):**
https://fastapi-zero-dh8f.onrender.com/docs

> A API roda no plano gratuito do Render: se ela estiver "dormindo", a
> primeira requisição pode levar até ~1 minuto para responder.

## ✨ Funcionalidades

- CRUD de **usuários**, com senhas guardadas como hash (**Argon2**)
- **Login com JWT**, rotas protegidas, expiração e **renovação** do token
- **Autorização**: cada usuário só altera/apaga a própria conta e as
  próprias tarefas
- CRUD de **tarefas**, com filtros (título, descrição, estado),
  paginação e atualização parcial (`PATCH`)
- Aplicação **assíncrona** de ponta a ponta (`async`/`await`)
- Esquema do banco versionado com **migrações do Alembic**

## 🛠️ Tecnologias

| Camada | Ferramentas |
|---|---|
| API | FastAPI, Pydantic, pydantic-settings |
| Banco de dados | PostgreSQL, SQLAlchemy 2 (async), psycopg 3, Alembic |
| Segurança | PyJWT, pwdlib (Argon2) |
| Testes | Pytest, pytest-asyncio, pytest-cov, factory-boy, freezegun, testcontainers |
| Qualidade | Ruff (lint e formatação), taskipy |
| Infra | Docker, Docker Compose, GitHub Actions, Render, Supabase |

## 📌 Rotas

| Método | Rota | Token? | Descrição |
|---|---|:---:|---|
| `GET` | `/` | | Rota de saúde (`Hello World`) |
| `POST` | `/users/` | | Cadastra um usuário |
| `GET` | `/users/` | 🔒 | Lista usuários (paginado) |
| `GET` | `/users/{user_id}` | | Busca um usuário pelo id |
| `PUT` | `/users/{user_id}` | 🔒 | Atualiza o próprio usuário |
| `DELETE` | `/users/{user_id}` | 🔒 | Remove o próprio usuário |
| `POST` | `/auth/token` | | Login: devolve o token JWT |
| `POST` | `/auth/refresh_token` | 🔒 | Renova o token |
| `POST` | `/todos/` | 🔒 | Cria uma tarefa |
| `GET` | `/todos/` | 🔒 | Lista as tarefas do usuário (filtros + paginação) |
| `PATCH` | `/todos/{todo_id}` | 🔒 | Altera campos de uma tarefa |
| `DELETE` | `/todos/{todo_id}` | 🔒 | Apaga uma tarefa |

Estados possíveis de uma tarefa: `draft`, `todo`, `doing`, `done` e
`trash`.

## 🚀 Como rodar localmente

Pré-requisitos: **Python 3.13**, **Poetry** e **Docker**.

1. Clone o repositório e instale as dependências:

   ```bash
   git clone https://github.com/Lucasrlcaldeira/fastapi_zero.git
   cd fastapi_zero
   poetry install
   ```

2. Crie um arquivo `.env` na raiz:

   ```env
   DATABASE_URL="postgresql+psycopg://app_user:app_password@localhost:5432/app_db"
   SECRET_KEY="troque-por-uma-chave-secreta"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. Suba a aplicação:

   **Opção A — tudo no Docker** (API + PostgreSQL, com migrações
   aplicadas automaticamente):

   ```bash
   docker compose up --build
   ```

   **Opção B — só o banco no Docker e a API no seu terminal** (recarrega
   a cada alteração no código):

   ```bash
   docker compose up -d fastzero_database
   poetry run alembic upgrade head
   poetry run task run
   ```

4. Acesse http://localhost:8000/docs

## 🧪 Testes e qualidade

Os testes sobem um PostgreSQL descartável com **testcontainers**, então o
Docker precisa estar aberto.

```bash
poetry run task test     # lint + testes + relatório de cobertura (htmlcov/)
poetry run task lint     # ruff check
poetry run task format   # ruff check --fix + ruff format
```

## ⚙️ CI/CD e deploy

- **CI:** a cada push ou pull request, o GitHub Actions instala o projeto
  e roda format, lint e testes
  ([`pipeline.yml`](.github/workflows/pipeline.yml)).
- **Deploy:** a API roda no **Render** (a partir do `Dockerfile`, com
  deploy automático a cada push na `master`) e o banco PostgreSQL fica no
  **Supabase**.

## 📚 Créditos

Projeto desenvolvido seguindo o curso
[FastAPI do Zero](https://fastapidozero.dunossauro.com/), de Eduardo
Mendes ([@dunossauro](https://github.com/dunossauro)).

Quer entender cada arquivo do projeto? Veja o
[`GUIA_DO_PROJETO.md`](GUIA_DO_PROJETO.md).
