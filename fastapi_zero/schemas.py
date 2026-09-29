# BaseModel: classe base do Pydantic — toda classe que herda dela
# ganha validação automática de tipos.
# ConfigDict: usado para configurar o comportamento de um schema.
# EmailStr: tipo especial que valida se o texto tem formato de e-mail
# válido (ex: precisa ter "@" e domínio).
from pydantic import BaseModel, ConfigDict, EmailStr


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
