from pydantic import BaseModel, ConfigDict, EmailStr

# BaseModel: classe base do Pydantic — toda classe que herda dela
# ganha validação automática de tipos.
# EmailStr: tipo especial que valida se o texto tem formato de e-mail
# válido (ex: precisa ter "@" e domínio).


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


class UserList(BaseModel):
    # Formato da resposta da rota que lista usuários: um objeto com a
    # chave "users" contendo uma lista de UserPublic.
    users: list[UserPublic]
