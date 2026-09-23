# Guia do Projeto — fastapi_zero

Este arquivo explica, de forma didática, o que cada arquivo do projeto faz.
Serve como material de apoio para o curso de FastAPI que você está fazendo.

---

## 📁 Raiz do projeto

### `pyproject.toml`
É o "documento de identidade" do projeto, gerenciado pelo **Poetry**
(gerenciador de dependências e pacotes do Python). Nele estão definidos:

- Nome do projeto (`fastapi-zero`), versão, autor.
- Versão mínima do Python exigida (3.13+).
- **Dependências de produção**: FastAPI, SQLAlchemy, Pydantic Settings,
  Alembic.
- **Dependências de desenvolvimento**: Ruff (lint/formatação), Pytest
  (testes), pytest-cov (cobertura de testes), Taskipy (atalhos de comando).
- Configurações do Ruff: linha máxima de 79 caracteres, aspas simples.
- Atalhos de comando via `task` (Taskipy), por exemplo:
  - `task run` → sobe o servidor de desenvolvimento.
  - `task test` → roda os testes com cobertura.
  - `task lint` → verifica o código com o Ruff.
  - `task format` → formata o código automaticamente.

### `poetry.lock`
Arquivo gerado **automaticamente** pelo Poetry. Ele trava as versões exatas
de cada dependência (e das subdependências delas), garantindo que qualquer
pessoa que instale o projeto tenha exatamente as mesmas versões que você.
**Nunca edite este arquivo manualmente.**

### `.env`
Guarda variáveis de ambiente — configurações sensíveis ou que mudam entre
ambientes (dev, produção, etc.), mantidas fora do código-fonte. Aqui contém
apenas:
```
DATABASE_URL = 'sqlite:///database.db'
```
Ou seja, diz ao projeto para usar um banco de dados **SQLite** local,
guardado no arquivo `database.db`.

### `.gitignore`
Lista de arquivos e pastas que o **Git** deve ignorar (não versionar), como
`__pycache__/`, `.venv/`, `.env`, `database.db`, caches de ferramentas
(`.ruff_cache`, `.pytest_cache`), etc. Evita que "lixo" ou dados sensíveis
sejam enviados ao repositório.

### `alembic.ini`
Arquivo de configuração do **Alembic**, a ferramenta que gerencia
**migrações de banco de dados** (mudanças estruturais versionadas, como
"criar a tabela X" ou "adicionar a coluna Y"). Define onde ficam os
scripts de migração (pasta `migrations/`) e as configurações de log. A URL
real do banco é sobrescrita dinamicamente pelo código Python em
`migrations/env.py` (que lê do `.env`).

### `database.db`
O arquivo físico do banco de dados SQLite. É criado/atualizado quando as
migrações rodam ou a aplicação salva dados. É um **artefato gerado**, não
faz parte do código-fonte que você escreve.

### `README.md`
Está vazio no momento — ainda não há documentação escrita sobre o projeto.

### `.coverage`
Arquivo binário gerado automaticamente pelo `pytest-cov` com os dados
brutos de cobertura de testes (quais linhas do código foram executadas
durante os testes). É consumido para gerar o relatório em `htmlcov/`.

---

## 📁 `fastapi_zero/` — o código da aplicação

Esta é a pasta principal do pacote Python da aplicação.

### `app.py`
O **coração da API**. Aqui é criada a instância do FastAPI
(`app = FastAPI()`) e definidas todas as rotas (endpoints):

| Rota | Método | O que faz |
|---|---|---|
| `/` | GET | Retorna `{"message": "Hello World"}` (rota de teste/saúde) |
| `/users/` | POST | Cria um novo usuário |
| `/users/` | GET | Lista todos os usuários |
| `/users/{user_id}` | PUT | Atualiza um usuário pelo ID |
| `/users/{user_id}` | DELETE | Remove um usuário pelo ID |
| `/users/{user_id}` | GET | Busca um usuário específico pelo ID |

⚠️ **Importante**: neste estágio do curso, os usuários ainda são guardados
numa lista Python em memória (`database = []`), **não** no banco de dados
SQLite de verdade. Isso é comum nas primeiras aulas, antes de integrar o
SQLAlchemy nas rotas. As rotas de `PUT`, `DELETE` e `GET` por ID retornam
erro `404 Not Found` se o `user_id` não existir na lista.

### `models.py`
Define o **modelo `User`** usando o SQLAlchemy (ORM — Object-Relational
Mapper, que mapeia classes Python para tabelas do banco de dados). A tabela
`users` tem as colunas:

- `id`: chave primária, gerada automaticamente.
- `username`: texto único (não pode repetir).
- `email`: texto único (não pode repetir).
- `password`: texto.
- `created_at`: data/hora de criação, preenchida automaticamente pelo
  próprio banco (`server_default=func.now()`).

Usa o estilo moderno do SQLAlchemy 2.0, com `Mapped` (tipagem) e
`mapped_as_dataclass` (transforma a classe num dataclass Python, o que
facilita comparações e criação de instâncias).

### `schemas.py`
Define os **"contratos" de dados** da API usando Pydantic — cada classe é
validada automaticamente (tipos, formatos, obrigatoriedade):

- `Message`: formato de resposta simples, `{"message": str}`.
- `UserSchemas`: dados que o **cliente envia** para criar/atualizar um
  usuário (`username`, `email`, `password`).
- `UserPublic`: dados que a API **devolve** ao cliente — repare que **não
  inclui a senha**, por segurança!
- `UserDB`: representação interna do usuário, com `id` incluso (herda de
  `UserSchemas`).
- `UserList`: uma lista de `UserPublic`, usada na rota de listagem
  (`GET /users/`).

### `settings.py`
Lê as variáveis de ambiente do arquivo `.env` de forma **tipada e
validada**, usando a biblioteca `pydantic-settings`. Atualmente expõe
apenas `DATABASE_URL`, que é usada pelo Alembic (e futuramente pela
aplicação) para saber a qual banco se conectar.

### `__init__.py`
Arquivo vazio. Sua única função é marcar a pasta `fastapi_zero` como um
**pacote Python** importável (permite fazer `from fastapi_zero.app import app`,
por exemplo).

---

## 📁 `migrations/` — histórico de mudanças no banco (Alembic)

### `env.py`
Script que o Alembic executa para saber **como conectar** ao banco e **o
que versionar**. Ele:
1. Pega a URL do banco de dados das `Settings` (que lê do `.env`).
2. Aponta o "metadata" dos models (`table_registry.metadata`) como fonte
   da verdade, permitindo que o Alembic **gere migrações automaticamente**
   ao comparar os models com o estado atual do banco.

### `script.py.mako`
Um **template** (modelo) usado pelo Alembic para gerar novos arquivos de
migração. Contém placeholders (`${...}`) que são preenchidos
automaticamente toda vez que você roda `alembic revision`.

### `versions/2ba89507e184_create_users_table.py`
A primeira (e, por enquanto, única) **migração real** do projeto. Define
duas funções:
- `upgrade()`: cria a tabela `users` com todas as suas colunas e
  restrições (chave primária, campos únicos).
- `downgrade()`: desfaz essa mudança, removendo a tabela — usado caso você
  precise "voltar no tempo" o esquema do banco.

Cada migração é como um "commit do Git", mas para a estrutura do banco de
dados.

### `README`
Um texto padrão de uma linha, gerado automaticamente pelo Alembic ao
inicializar a pasta de migrações. Não tem conteúdo específico do projeto.

---

## 📁 `tests/` — testes automatizados

### `conftest.py`
Define as **fixtures** do Pytest — funções que preparam dados/objetos
reutilizáveis pelos testes (o Pytest as injeta automaticamente quando o
teste pede o nome como parâmetro):

- `client`: um cliente HTTP de teste (`TestClient`) que simula requisições
  (`GET`, `POST`, etc.) à API **sem precisar subir um servidor real**.
- `session`: cria um banco de dados SQLite **temporário, em memória**
  (`sqlite:///:memory:`) para cada teste — rápido e isolado. Cria as
  tabelas antes do teste rodar e as apaga depois, garantindo que cada
  teste comece com um banco limpo.
- `mock_db_time`: um truque (usando eventos do SQLAlchemy) para "congelar"
  o campo `created_at` numa data fixa durante os testes, evitando que
  testes falhem por causa da hora exata em que rodaram.

### `test_app.py`
Testa as **rotas da API** definidas em `app.py`:
- Rota raiz (`/`).
- Criação de usuário (`POST /users/`).
- Listagem de usuários (`GET /users/`).
- Atualização de usuário (`PUT /users/{id}`).
- Remoção de usuário (`DELETE /users/{id}`).
- Casos de erro `404` quando o usuário não existe.

Há dois testes comentados no final do arquivo (`test_exercicio_ok` e
`test_exercicio_not_ok`), que parecem ser **exercícios do curso ainda não
implementados** — provavelmente testando a rota `GET /users/{user_id}`.

### `test_db.py`
Testa o **modelo `User`** diretamente no banco de dados (sem passar pela
API): cria um usuário, salva na sessão do banco e confere se os dados
batem, usando a fixture `mock_db_time` para fixar a data de criação e
tornar o teste previsível.

### `__init__.py`
Arquivo vazio, apenas marca a pasta `tests` como um pacote Python.

---

## 📁 Pastas geradas automaticamente (não são código-fonte)

Estas pastas são criadas por ferramentas e **não precisam ser estudadas**
nem editadas manualmente — normalmente ficam no `.gitignore`:

- **`.idea/`** — configurações do PyCharm (IDE JetBrains).
- **`.pytest_cache/`** — cache interno do Pytest entre execuções.
- **`.ruff_cache/`** — cache interno do Ruff (linter/formatador).
- **`htmlcov/`** — relatório de cobertura de testes em HTML, gerado por
  `task test` → abra `htmlcov/index.html` no navegador para visualizar
  quais linhas do código foram (ou não) testadas.

---

## 🧭 Resumo geral do projeto

É uma API FastAPI de estudo (o nome sugere o curso **"FastAPI do Zero"**)
que implementa um **CRUD de usuários** (Create, Read, Update, Delete).

O projeto está em uma fase de **transição**:
- As rotas em `app.py` ainda usam uma **lista Python em memória** como
  "banco de dados" (dados somem quando o servidor reinicia).
- A infraestrutura para o banco de dados **real** já está pronta e
  testada: o model SQLAlchemy (`models.py`), as migrações do Alembic
  (`migrations/`) e os testes de banco (`test_db.py`).

O próximo passo natural do curso deve ser **conectar as rotas de
`app.py` ao banco de dados real** (usando `Session` do SQLAlchemy),
substituindo a lista `database = []` por consultas de verdade ao SQLite.
