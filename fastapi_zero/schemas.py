# Tipo de data e hora, usado nos campos created_at e updated_at das
# tarefas.
from datetime import datetime

# BaseModel: classe base do Pydantic — toda classe que herda dela
# ganha validação automática de tipos.
# ConfigDict: usado para configurar o comportamento de um schema.
# EmailStr: tipo especial que valida se o texto tem formato de e-mail
# válido (ex: precisa ter "@" e domínio).
# Field: adiciona regras extras a um campo (valor padrão, mínimo,
# tamanho mínimo do texto etc.).
from pydantic import BaseModel, ConfigDict, EmailStr, Field

# O mesmo Enum do model, reaproveitado aqui para que a API só aceite
# estados válidos (draft, todo, doing, done, trash).
from fastapi_zero.models import TodoState


class Message(BaseModel):
    message: str
    # Schema usado pela rota "/" — só tem um campo de texto.


class UserSchemas(BaseModel):
    # Dados que o CLIENTE envia para criar ou atualizar um usuário.
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    # Dados que a API DEVOLVE ao cliente. Note que não tem "password" —
    # isso garante que a senha nunca vaze nas respostas da API.
    username: str
    email: EmailStr
    id: int
    model_config = ConfigDict(from_attributes=True)
    # from_attributes=True permite criar o schema a partir de um OBJETO
    # (como o model User do SQLAlchemy), lendo user.username,
    # user.email... em vez de exigir um dicionário.


class UserList(BaseModel):
    # Formato da resposta da rota que lista usuários: um objeto com a
    # chave "users" contendo uma lista de UserPublic.
    users: list[UserPublic]


class Token(BaseModel):
    # Resposta da rota de login (POST /token).
    access_token: str
    # O token JWT em si (um texto longo, em 3 partes separadas por ".").
    token_type: str
    # O tipo do token; aqui sempre "Bearer".


class FilterPage(BaseModel):
    # Parâmetros de paginação, lidos da URL (?offset=0&limit=10).
    offset: int = Field(ge=0, default=0)
    # Quantos registros pular. ge=0 ("greater or equal") recusa
    # números negativos.
    limit: int = Field(ge=0, default=10)
    # Quantos registros devolver, no máximo.


class FilterTodo(FilterPage):
    # Filtros da listagem de tarefas. Herda de FilterPage, então também
    # tem offset e limit, sem precisar repetir.
    title: str | None = Field(default=None, min_length=3, max_length=20)
    # "str | None" = pode ser texto OU nada. O padrão None quer dizer
    # "o usuário não pediu esse filtro" (é o que os ifs da rota checam).
    # min_length=3: buscas com menos de 3 letras dão erro 422.
    description: str | None = None
    state: TodoState | None = None


class TodoSchema(BaseModel):
    # Dados que o CLIENTE envia para criar uma tarefa.
    title: str
    description: str
    state: TodoState = Field(default=TodoState.todo)
    # Se o cliente não mandar o estado, a tarefa começa como "todo".


class TodoPublic(TodoSchema):
    # O que a API DEVOLVE: tudo do TodoSchema + o id e as datas, que só
    # existem depois que o banco salva a tarefa.
    id: int
    created_at: datetime
    updated_at: datetime
    # Datas preenchidas pelo próprio banco (veja o model Todo). No JSON,
    # o datetime vira texto no formato ISO: "2026-09-18T00:00:00".


class TodoList(BaseModel):
    # Resposta da listagem: {"todos": [tarefa, tarefa, ...]}.
    todos: list[TodoPublic]


class TodoUpdate(BaseModel):
    # Dados do PATCH. Todos os campos são opcionais, porque o cliente
    # manda só o que quer mudar (ex: só {"state": "done"}).
    title: str | None = None
    description: str | None = None
    state: TodoState | None = None
