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
- **Dependências de produção**:
  - `fastapi[standard]` — o framework da API.
  - `sqlalchemy[asyncio]` — ORM para conversar com o banco de dados. O
    extra `[asyncio]` instala o que é preciso para usar o SQLAlchemy no
    modo **assíncrono** (`AsyncSession`, `create_async_engine`).
  - `aiosqlite` — driver **assíncrono** do SQLite. O driver padrão do
    Python (`sqlite3`) é síncrono e não funciona com o engine async.
  - `pydantic-settings` — leitura das configurações do `.env`.
  - `alembic` — migrações do banco de dados.
  - `pwdlib[argon2]` — gera e confere **hashes de senha** (algoritmo
    Argon2).
  - `pyjwt` — cria e valida os **tokens JWT** usados no login.
  - `tzdata` — base de fusos horários (necessária no Windows para o
    `ZoneInfo('UTC')` usado no `security.py`).
- **Dependências de desenvolvimento**: Ruff (lint/formatação), Pytest
  (testes), pytest-cov (cobertura de testes), Taskipy (atalhos de comando)
  e pytest-asyncio (permite escrever testes e fixtures com `async def`).
- Configurações do Ruff: linha máxima de 79 caracteres, aspas simples.
- Configurações do Pytest: `asyncio_default_fixture_loop_scope =
  'function'` faz cada teste ganhar o seu próprio **loop de eventos**
  (veja a seção ⚡ mais abaixo), assim um teste não interfere no outro.
- Configuração do coverage: `concurrency = ['thread', 'greenlet']`. O
  SQLAlchemy async usa *greenlets* por baixo dos panos; sem essa opção, o
  pytest-cov não "enxerga" algumas linhas executadas e a cobertura sai
  errada.
- Atalhos de comando via `task` (Taskipy), por exemplo:
  - `task run` → sobe o servidor de desenvolvimento.
  - `task test` → roda o lint, depois os testes com cobertura, e por fim
    gera o relatório HTML (`pre_test` e `post_test` rodam sozinhos).
  - `task lint` → verifica o código com o Ruff.
  - `task format` → corrige o que dá automaticamente e formata o código.

### `poetry.lock`
Arquivo gerado **automaticamente** pelo Poetry. Ele trava as versões exatas
de cada dependência (e das subdependências delas), garantindo que qualquer
pessoa que instale o projeto tenha exatamente as mesmas versões que você.
**Nunca edite este arquivo manualmente.**

### `.env`
Guarda variáveis de ambiente — configurações sensíveis ou que mudam entre
ambientes (dev, produção, etc.), mantidas fora do código-fonte. Aqui contém
quatro variáveis:

- `DATABASE_URL='sqlite+aiosqlite:///database.db'` — diz ao projeto para
  usar um banco de dados **SQLite** local, guardado no arquivo
  `database.db`. O `+aiosqlite` escolhe o **driver assíncrono** — sem
  ele, o `create_async_engine` dá erro.
- `SECRET_KEY` — a chave secreta que **assina** os tokens JWT. Quem
  conhece essa chave consegue criar tokens válidos, por isso ela fica
  aqui e não no código.
- `ALGORITHM` — o algoritmo de assinatura do JWT.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — por quantos minutos o token vale.

### `.gitignore`
Lista de arquivos e pastas que o **Git** deve ignorar (não versionar), como
`__pycache__/`, `.venv/`, `.env`, `database.db`, caches de ferramentas
(`.ruff_cache`, `.pytest_cache`), etc. Evita que "lixo" ou dados sensíveis
sejam enviados ao repositório.

> 💡 As primeiras linhas do arquivo (`Collecting ignr`, `Downloading...`)
> são sobra da saída do comando que gerou o `.gitignore`. Não atrapalham
> (o Git as trata como padrões que não casam com nada), mas podem ser
> apagadas.

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
Quando for publicar no GitHub, vale preencher (veja o fim deste guia).

### `.coverage`
Arquivo binário gerado automaticamente pelo `pytest-cov` com os dados
brutos de cobertura de testes (quais linhas do código foram executadas
durante os testes). É consumido para gerar o relatório em `htmlcov/`.

---

## 📁 `fastapi_zero/` — o código da aplicação

Esta é a pasta principal do pacote Python da aplicação.

### `app.py`
O **ponto de partida da API**. Aqui é criada a instância do FastAPI
(`app = FastAPI()`), que é "plugada" nos routers com
`app.include_router(auth.router)`, `app.include_router(users.router)` e
`app.include_router(todos.router)`.
O próprio `app.py` só define a rota raiz (`/`); as outras rotas ficam na
pasta `routers/`.

### `routers/` — as rotas, separadas por assunto
Um **`APIRouter`** é como um "mini-app": agrupa rotas do mesmo assunto
num arquivo próprio. O `prefix` é colocado na frente de todas as rotas do
router, e as `tags` agrupam as rotas na documentação (`/docs`).

- `routers/auth.py` — `APIRouter(prefix='/auth')`: **login** e
  **renovação do token**.
- `routers/users.py` — `APIRouter(prefix='/users')`: o **CRUD de
  usuários**.
- `routers/todos.py` — `APIRouter(prefix='/todos')`: o **CRUD de
  tarefas** (lista de afazeres). Todas as rotas exigem token, e cada
  usuário só enxerga e mexe nas **próprias** tarefas.

Os arquivos definem o atalho `Session = Annotated[AsyncSession,
Depends(get_session)]`, que junta o tipo e a dependência num nome só, e
o `CurrentUser`, que faz o mesmo com o `get_current_user`.

Todas as rotas da API:

| Rota | Método | Arquivo | Precisa de token? | O que faz |
|---|---|---|---|---|
| `/` | GET | `app.py` | Não | Retorna `{"message": "Hello World"}` (rota de teste/saúde) |
| `/users/` | POST | `routers/users.py` | Não | Cria um novo usuário (cadastro) |
| `/users/` | GET | `routers/users.py` | **Sim** | Lista os usuários, com paginação (`limit`/`offset`) |
| `/users/{user_id}` | GET | `routers/users.py` | Não | Busca um usuário específico pelo ID |
| `/users/{user_id}` | PUT | `routers/users.py` | **Sim** | Atualiza o **próprio** usuário |
| `/users/{user_id}` | DELETE | `routers/users.py` | **Sim** | Remove o **próprio** usuário |
| `/auth/token` | POST | `routers/auth.py` | Não | Login: recebe e-mail e senha e devolve um token JWT |
| `/auth/refresh_token` | POST | `routers/auth.py` | **Sim** | Troca um token ainda válido por um novo, com prazo renovado |
| `/todos/` | POST | `routers/todos.py` | **Sim** | Cria uma tarefa para o usuário logado |
| `/todos/` | GET | `routers/todos.py` | **Sim** | Lista as tarefas do usuário logado, com filtros e paginação |
| `/todos/{todo_id}` | PATCH | `routers/todos.py` | **Sim** | Altera só os campos enviados de uma tarefa |
| `/todos/{todo_id}` | DELETE | `routers/todos.py` | **Sim** | Apaga uma tarefa |

Pontos importantes:

- Todas as rotas usam o **banco de dados real** através de uma sessão do
  SQLAlchemy, recebida com `Depends(get_session)`.
- As rotas são **assíncronas** (`async def`) e usam `await` em toda
  chamada que vai ao banco (`scalar`, `scalars`, `commit`, `refresh`,
  `delete`). O `session.add()` **não** leva `await`, porque só mexe na
  memória.
- As senhas são salvas como **hash** (`get_password_hash`), nunca como
  texto puro.
- Rotas protegidas pedem `Depends(get_current_user)`. Sem um token válido
  no header `Authorization: Bearer <token>`, elas devolvem **401**.
- No `PUT` e no `DELETE`, se o `user_id` da URL for diferente do usuário
  logado, a resposta é **403 (Forbidden)**: cada um só mexe na própria
  conta.
- Tentar cadastrar ou atualizar para um username/e-mail que já existe
  devolve **409 (Conflict)**.
- No login, o campo do formulário se chama `username` (é o padrão do
  OAuth2), mas o valor esperado é o **e-mail**.
- Nas tarefas, quem tenta apagar ou alterar uma tarefa de **outra
  pessoa** recebe **404**, como se ela não existisse. A busca sempre
  exige as duas coisas: `Todo.id == todo_id` **e**
  `Todo.user_id == user.id`.

#### 📝 Como funciona a listagem de tarefas (`GET /todos/`)

Os filtros chegam pela URL e viram um `FilterTodo` (graças ao
`Query()`). Ex: `GET /todos/?title=mercado&limit=5`.

1. A rota começa com uma consulta base, que ainda **não foi ao banco**:
   `select(Todo).where(Todo.user_id == user.id)`.
2. Cada `if` acrescenta um filtro **só se** ele foi enviado (quando não
   vem na URL, o valor é `None` e o `if` é pulado).
3. `.contains(texto)` vira `LIKE '%texto%'` no SQL: acha o texto em
   qualquer parte do campo.
4. `.filter()` devolve uma **query nova**, por isso o
   `query = query.filter(...)`.
5. No fim, `limit`/`offset` fazem a paginação e o `await
   session.scalars(...)` finalmente executa a consulta.

| URL | SQL gerado (resumido) |
|---|---|
| `/todos/` | `WHERE user_id = 1` |
| `/todos/?title=mercado` | `WHERE user_id = 1 AND title LIKE '%mercado%'` |
| `/todos/?title=mercado&state=done` | `... AND title LIKE '%mercado%' AND state LIKE '%done%'` |

#### ✏️ PUT × PATCH

- **PUT** (em `users.py`) substitui o registro **inteiro**: todos os
  campos precisam ser enviados.
- **PATCH** (em `todos.py`) muda **só os campos enviados**. O truque é
  `todo.model_dump(exclude_unset=True)`, que monta um dicionário só com
  o que o cliente mandou, e o `setattr`, que aplica cada campo no
  objeto do banco.

#### Códigos HTTP usados no projeto

| Código | Nome | Quando aparece |
|---|---|---|
| 200 | OK | Deu certo |
| 201 | Created | Usuário criado |
| 401 | Unauthorized | Token ausente/inválido ou senha errada — "não sei quem você é" |
| 403 | Forbidden | Logado, mas sem permissão — "sei quem você é, mas não pode" |
| 404 | Not Found | Usuário ou tarefa não encontrados (ou tarefa de outra pessoa) |
| 422 | Unprocessable Entity | Dados inválidos (ex: filtro `title` curto ou longo demais, `state` que não existe) |
| 409 | Conflict | Username ou e-mail já cadastrado |

### `security.py`
Concentra tudo o que é **segurança**:

- `get_password_hash(password)`: transforma a senha em hash (Argon2). O
  hash é irreversível e muda a cada chamada, por causa do *salt*
  aleatório.
- `verify_password(senha, hash)`: confere se a senha digitada corresponde
  ao hash salvo.
- `create_access_token(data)`: cria um **token JWT** com os dados
  recebidos + o campo `exp` (expira depois de
  `ACCESS_TOKEN_EXPIRE_MINUTES` minutos), assinado com a `SECRET_KEY` e
  o `ALGORITHM`. Os três valores vêm do `Settings` (ou seja, do `.env`).
- `oauth2_scheme`: ensina o FastAPI a pegar o token do header
  `Authorization` e faz aparecer o botão **Authorize** no `/docs`.
- `get_current_user(...)`: **dependência** das rotas protegidas. Decodifica
  o token, lê o e-mail guardado em `sub` e busca o usuário no banco. Se
  algo falhar (token malformado, **vencido** ou de usuário que não existe
  mais), devolve 401. É `async def`, porque a busca no banco usa
  `await`.

**Como funciona o login, passo a passo:**
1. O cliente faz `POST /auth/token` com e-mail e senha (form-data).
2. A API confere a senha com `verify_password`.
3. Se estiver certa, gera um token com `{'sub': email}` e devolve.
4. Nas próximas requisições, o cliente manda o header
   `Authorization: Bearer <token>`.
5. `get_current_user` valida o token e entrega o usuário para a rota.
6. Antes de o token vencer, o cliente pode chamar
   `POST /auth/refresh_token` para ganhar um token novo sem digitar a
   senha de novo. Token já vencido não pode ser renovado (dá 401).

> ⚠️ **Sobre o JWT**: o conteúdo do token **não é secreto** — qualquer um
> pode decodificá-lo (teste em jwt.io). A assinatura só garante que ele
> **não foi alterado**. Por isso nunca coloque a senha dentro do token.

> ⚠️ **Sobre a `SECRET_KEY`**: ela fica no `.env`, que está no
> `.gitignore`, então nunca vai para o GitHub. Se alguém descobrir essa
> chave, consegue criar tokens válidos em nome de qualquer usuário.

### `database.py`
Cria a conexão com o banco:

- `engine`: o "motor" de conexão, criado **uma vez** com a
  `DATABASE_URL` do `.env`, usando `create_async_engine` (versão
  assíncrona).
- `get_session()`: dependência **assíncrona** (`async def`) que abre uma
  `AsyncSession` para cada requisição, entrega para a rota com `yield` e
  fecha ao final (graças ao `async with`). Nos testes, ela é trocada por
  uma sessão de banco em memória.
- `expire_on_commit=False`: por padrão, depois do `commit` o SQLAlchemy
  "esquece" os valores dos objetos e os relê do banco no próximo acesso.
  No modo async essa releitura escondida não é possível (ela precisaria
  de um `await`), então esse comportamento é desligado.

### ⚡ Programação assíncrona (`async`/`await`) — resumo

- **Síncrono**: enquanto a rota espera o banco responder, o servidor fica
  parado esperando junto.
- **Assíncrono**: enquanto a rota espera (`await`), o servidor fica livre
  para atender **outras requisições**. Quando a resposta chega, a rota
  continua de onde parou.
- `async def` cria uma **corrotina** — uma função que pode ser "pausada"
  nos `await`.
- `await` só pode ser usado **dentro** de uma função `async def`. Esquecer
  o `await` não dá erro na hora: a variável recebe uma corrotina pendente
  em vez do resultado (ex: `user` não seria um `User`).
- `async with` é o `with` do mundo assíncrono (abre e fecha recursos com
  `await` por baixo dos panos).
- O **loop de eventos** é quem gerencia essas pausas e retomadas. O
  FastAPI já cuida dele nas rotas; nos testes, quem cuida é o
  pytest-asyncio; no Alembic, o `asyncio.run()`.
- `run_sync(funcao)`: executa uma função **síncrona** (como
  `metadata.create_all` ou as migrações do Alembic) "por dentro" de uma
  conexão assíncrona — é a ponte entre os dois mundos.

### `models.py`
Define os **modelos `User` e `Todo`** usando o SQLAlchemy (ORM —
Object-Relational Mapper, que mapeia classes Python para tabelas do banco
de dados). A tabela `users` tem as colunas:

- `id`: chave primária, gerada automaticamente.
- `username`: texto único (não pode repetir).
- `email`: texto único (não pode repetir).
- `password`: o **hash** da senha.
- `created_at`: data/hora de criação, preenchida automaticamente pelo
  próprio banco (`server_default=func.now()`).
- `updated_at`: data/hora da última alteração. Preenchida na criação e
  atualizada a cada `UPDATE` (`onupdate=func.now()`).
- `todos`: **não é coluna**. É um `relationship`, um "atalho" para a
  lista de tarefas do usuário (`user.todos`). Com
  `cascade='all, delete-orphan'`, apagar o usuário apaga as tarefas dele.

A tabela `todos` tem as colunas:

- `id`: chave primária.
- `title` e `description`: textos da tarefa.
- `state`: o estado da tarefa. Só aceita os valores do `TodoState`
  (`draft`, `todo`, `doing`, `done`, `trash`), um `Enum` que herda de
  `str` para virar texto simples no JSON e no banco.
- `created_at` e `updated_at`: as mesmas datas automáticas do `User`
  (criação e última alteração), preenchidas pelo banco.
- `user_id`: **chave estrangeira** (`ForeignKey('users.id')`). Guarda o
  id do dono da tarefa e liga as duas tabelas: um usuário tem **várias**
  tarefas, e cada tarefa tem **um** dono (relação 1 para N).

Usa o estilo moderno do SQLAlchemy 2.0, com `Mapped` (tipagem) e
`mapped_as_dataclass` (transforma a classe num dataclass Python, o que
facilita comparações e criação de instâncias). Campos com `init=False`
(`id`, `created_at`, `updated_at`) não são passados na criação do objeto,
porque quem preenche é o banco.

### `schemas.py`
Define os **"contratos" de dados** da API usando Pydantic — cada classe é
validada automaticamente (tipos, formatos, obrigatoriedade):

- `Message`: formato de resposta simples, `{"message": str}`.
- `UserSchemas`: dados que o **cliente envia** para criar/atualizar um
  usuário (`username`, `email`, `password`).
- `UserPublic`: dados que a API **devolve** ao cliente — repare que **não
  inclui a senha**, por segurança! Tem `from_attributes=True`, que permite
  montá-lo direto a partir de um objeto `User` do SQLAlchemy.
- `UserList`: uma lista de `UserPublic`, usada na rota de listagem
  (`GET /users/`).
- `Token`: resposta do login, com `access_token` e `token_type`
  (`"Bearer"`).
- `FilterPage`: os parâmetros de **paginação** da listagem, lidos da URL
  (ex: `GET /users/?offset=0&limit=10`). `offset` diz quantos registros
  pular e `limit` quantos devolver. Os dois têm `Field(ge=0)`, ou seja,
  não aceitam números negativos (padrões: `offset=0`, `limit=10`).
- `FilterTodo`: os filtros da listagem de tarefas. **Herda** de
  `FilterPage` (ganha `offset` e `limit`) e acrescenta `title`,
  `description` e `state`, todos opcionais (`None` = "não filtrar por
  isso"). O `title` exige pelo menos 3 letras (`min_length=3`).
- `TodoSchema`: o que o cliente envia para **criar** uma tarefa. Se o
  `state` não vier, começa como `todo`.
- `TodoPublic`: o que a API **devolve**: o `TodoSchema` + o `id`, o
  `created_at` e o `updated_at` (as datas vão no JSON como texto ISO,
  ex: `"2026-09-18T00:00:00"`).
- `TodoList`: resposta da listagem, `{"todos": [...]}`.
- `TodoUpdate`: o corpo do **PATCH**, com todos os campos opcionais,
  porque o cliente manda só o que quer mudar.

### `settings.py`
Lê as variáveis de ambiente do arquivo `.env` de forma **tipada e
validada**, usando a biblioteca `pydantic-settings`. Expõe:

- `DATABASE_URL`: usada pelo `database.py` (aplicação) e pelo
  `migrations/env.py` (Alembic) para saber a qual banco se conectar.
- `SECRET_KEY`, `ALGORITHM` e `ACCESS_TOKEN_EXPIRE_MINUTES`: usadas pelo
  `security.py` para criar e validar os tokens JWT.

Se alguma dessas variáveis faltar no `.env`, a aplicação **nem sobe**.
Isso é proposital: é melhor falhar logo do que rodar com uma
configuração errada.

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
3. Conecta ao banco de forma **assíncrona**, já que a URL usa o driver
   `aiosqlite`. Como o Alembic em si só roda migrações de forma síncrona,
   o arquivo é dividido em três partes:
   - `do_run_migrations(connection)`: parte **síncrona**, que aplica as
     migrações numa conexão já aberta.
   - `run_async_migrations()`: parte **assíncrona**, que cria o engine
     com `async_engine_from_config`, abre a conexão e chama
     `connection.run_sync(do_run_migrations)`.
   - `run_migrations_online()`: usa `asyncio.run(...)` para rodar a parte
     assíncrona (funções async não rodam sozinhas, precisam de um loop de
     eventos).

### `script.py.mako`
Um **template** (modelo) usado pelo Alembic para gerar novos arquivos de
migração. Contém placeholders (`${...}`) que são preenchidos
automaticamente toda vez que você roda `alembic revision`.

### `versions/` — as migrações, em ordem
Cada migração é como um "commit do Git", mas para a estrutura do banco de
dados. Cada arquivo aponta para a anterior (`down_revision`), formando uma
corrente:

| Ordem | Arquivo | O que faz |
|---|---|---|
| 1 | `2ba89507e184_create_users_table.py` | Cria a tabela `users` (id, username, email, password, created_at) |
| 2 | `eebc2e224646_add_updated_at_to_users.py` | Adiciona a coluna `updated_at` |
| 3 | `ced0fbd8d4db_exercicio_02_aula_04.py` | Migração **vazia** (`pass`) — foi gerada no exercício, mas não havia mudança a aplicar |
| 4 | `99d8f5d0f16c_create_todos_table.py` | Cria a tabela `todos` (id, title, description, state, user_id), com a chave estrangeira para `users` |
| 5 | `a99cdc5af920_add_created_at_and_updated_at_to_todos.py` | Adiciona `created_at` e `updated_at` em `todos`, usando o **modo batch** (veja abaixo) |

> ⚠️ **SQLite e o modo batch**: o SQLite não deixa adicionar uma coluna
> numa tabela existente quando o valor padrão é "não constante", como
> `CURRENT_TIMESTAMP` (dá o erro *Cannot add a column with non-constant
> default*). A solução é o `with op.batch_alter_table('todos') as
> batch_op:`: o Alembic cria uma tabela nova já com as colunas, copia os
> dados, apaga a antiga e renomeia a nova. Se o `--autogenerate` gerar um
> `op.add_column` desse tipo, troque para o modo batch antes do
> `alembic upgrade head`.

Toda migração tem duas funções:
- `upgrade()`: aplica a mudança (`alembic upgrade head`).
- `downgrade()`: desfaz a mudança (`alembic downgrade -1`) — usado caso
  você precise "voltar no tempo" o esquema do banco.

Comandos mais usados:
- `alembic revision --autogenerate -m "mensagem"` → compara os models com
  o banco e gera uma nova migração.
- `alembic upgrade head` → aplica todas as migrações pendentes.

### `README`
Um texto padrão de uma linha, gerado automaticamente pelo Alembic ao
inicializar a pasta de migrações. Não tem conteúdo específico do projeto.

---

## 📁 `tests/` — testes automatizados

### `conftest.py`
Define as **fixtures** do Pytest — funções que preparam dados/objetos
reutilizáveis pelos testes (o Pytest as injeta automaticamente quando o
teste pede o nome como parâmetro). Uma fixture pode depender de outra:

- `session`: cria um banco de dados SQLite **temporário, em memória**
  (`sqlite+aiosqlite:///:memory:`) para cada teste — rápido e isolado.
  Cria as tabelas antes do teste rodar e as apaga depois (com
  `conn.run_sync(...)`, porque `create_all`/`drop_all` são síncronos).
  Usa `StaticPool` para que todas as conexões enxerguem o mesmo banco em
  memória. É uma fixture **assíncrona**, por isso usa o decorador
  `@pytest_asyncio.fixture` em vez do `@pytest.fixture` comum.
- `client`: um cliente HTTP de teste (`TestClient`) que simula requisições
  à API **sem subir um servidor real**. Usa
  `app.dependency_overrides` para trocar o `get_session` da aplicação pela
  sessão em memória — assim os testes **nunca tocam no `database.db`**.
- `user`: cria um usuário já salvo no banco de teste (com a senha em
  hash) e guarda a senha original em `user.clean_password`, para os
  testes conseguirem fazer login. Também é assíncrona
  (`@pytest_asyncio.fixture`), porque salva no banco com `await`.
- `other_user`: um **segundo** usuário, igual ao `user`. Serve para testar
  o que acontece quando alguém mexe em dados de outra pessoa (ex: 403 nos
  usuários, 404 nas tarefas).
- `token`: faz login com o `user` na rota `/auth/token` e devolve o token JWT,
  pronto para ser usado nas rotas protegidas.
- `mock_db_time`: um truque (usando eventos do SQLAlchemy) para "congelar"
  `created_at` e `updated_at` numa data fixa durante os testes, evitando
  que falhem por causa da hora exata em que rodaram. Recebe o model a
  "vigiar": `mock_db_time(model=User)` ou `mock_db_time(model=Todo)`.

Encadeamento das fixtures:
```
session ──► client ──► token
   └──────► user ─────────┘
```

### `test_app.py`
Testa a **rota raiz** (`/`) definida em `app.py`, que devolve
`{'message': 'Hello World'}`.

### `test_users.py`
Testa as **rotas de usuários** (`routers/users.py`):
- Criação de usuário (`POST /users/`) e erro 409 com e-mail repetido.
- Listagem de usuários com token (`GET /users/`).
- Atualização do próprio usuário (`PUT /users/{id}`) e erro 409 ao usar
  um username que já é de outra pessoa.
- Remoção do próprio usuário (`DELETE /users/{id}`).
- Erro 403 ao tentar alterar/remover outro usuário.
- Busca de um usuário pelo id (`GET /users/{id}`), um exercício do
  curso: `test_read_user_exercicio` confere o 200 e
  `test_exercicio_not_ok` confere o 404 quando o id não existe.

### `test_auth.py`
Testa o **login** e a **renovação do token**:
- `test_get_token`: login com e-mail e senha (formulário) devolve um
  `access_token` do tipo `Bearer`.
- `test_token_wrong_password` e `test_token_inexistent_user`: senha
  errada e e-mail não cadastrado.
- `test_token_expired_after_time`: um token vencido passa a dar 401.
- `test_refresh_token`: um token válido é trocado por um novo.
- `test_token_expired_dont_refresh`: token vencido **não** pode ser
  renovado.

### `test_todos.py`
Testa as **rotas de tarefas** (`routers/todos.py`). Usa a
**`TodoFactory`** (biblioteca `factory_boy`), uma "fábrica" que cria
tarefas com dados inventados: `TodoFactory.create_batch(5, ...)` cria 5
de uma vez, e dá para fixar campos (`title='Test todo 1'`).
- Criação de tarefa (`POST /todos/`), usando o `mock_db_time(model=Todo)`
  para congelar as datas e conseguir comparar o JSON inteiro.
- `test_create_todo_error`: grava direto no banco um `state='test'`, que
  não existe no `TodoState`. O SQLite aceita, mas na **leitura** o
  SQLAlchemy lança `LookupError`, e o `pytest.raises` confere isso.
- Exercícios da aula 06: filtro `title` com 1 letra (`min_length`) e com
  22 letras (`max_length`) devem dar **422**.
- Listagem: sem filtros, com paginação (`?offset=1&limit=2`) e com cada
  filtro (`title`, `description`, `state`). O teste de descrição busca
  só `desc` e acha `description`, mostrando o "contém" do `.contains()`.
- `DELETE`: apagar a própria tarefa, 404 para id inexistente e 404 ao
  tentar apagar a tarefa do `other_user`.
- `PATCH`: 404 para id inexistente e alteração só do título.

### `test_db.py`
Testa o **modelo `User`** diretamente no banco de dados (sem passar pela
API): cria um usuário, salva na sessão do banco e confere se os dados
batem, usando a fixture `mock_db_time` para fixar `created_at` e
`updated_at` e tornar o teste previsível. Como usa a sessão assíncrona
direto, o teste é `async def` e leva a marca `@pytest.mark.asyncio`, que
pede ao pytest-asyncio para rodá-lo num loop de eventos.

> 💡 Testes que só usam o `TestClient` podem ser síncronos: ele cuida da
> parte assíncrona da API sozinho. Já os testes que salvam algo direto no
> banco antes de chamar a API (como vários de `test_todos.py`) precisam
> ser `async def` com `@pytest.mark.asyncio`, por causa do
> `await session.commit()`.

### `test_security.py`
Testa a parte de **segurança**:
- `test_jwt`: gera um token com `create_access_token`, decodifica e
  confere se os dados e o campo `exp` estão lá.
- `test_jwt_invalid_token`: chama uma rota protegida com um token falso e
  espera **401**.
- `test_get_current_user_not_found__exercicio`: token válido, mas sem o
  campo `sub` — espera **401**.
- `test_get_current_user_does_not_exists__exercicio`: token válido com
  `sub` de um e-mail que não está cadastrado — espera **401**.

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

É uma API FastAPI de estudo (curso **"FastAPI do Zero"**, do Dunossauro)
que implementa um **CRUD de usuários** e um **CRUD de tarefas** (Create,
Read, Update, Delete) com **autenticação por JWT**.

O que já está pronto:
- ✅ Rotas conectadas ao **banco de dados real** (SQLite via SQLAlchemy).
- ✅ Aplicação **assíncrona** (`async`/`await`) de ponta a ponta: rotas,
  sessão do banco, testes e migrações.
- ✅ Estrutura do banco versionada com **migrações do Alembic**.
- ✅ Senhas guardadas com **hash (Argon2)**.
- ✅ **Login** com token JWT, rotas **protegidas**, token que **expira**
  e **renovação** do token.
- ✅ Regra de **autorização**: cada usuário só altera/apaga a si mesmo.
- ✅ **Lista de tarefas** por usuário, com filtros, paginação e PATCH.
- ✅ **Testes automatizados** isolados, usando banco em memória.

Pontos que ainda podem evoluir (alguns aparecem nas próximas aulas do
curso):
- No login, usar 401 também quando o e-mail não existe (hoje é 404), para
  não revelar quais e-mails estão cadastrados.
- Escrever o `README.md` (o que o projeto faz, como instalar, como rodar e
  testar) — importante para o portfólio no GitHub.
