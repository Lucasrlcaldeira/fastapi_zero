from http import HTTPStatus

# HTTPStatus traz os códigos HTTP com nomes legíveis (OK, CREATED,
# NOT_FOUND...) em vez de números "mágicos" como 200, 201, 404.
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User

# FastAPI: classe usada para criar a aplicação web.
# HTTPException: usada para interromper uma rota e devolver um erro HTTP.
from fastapi_zero.schemas import (
    Message,
    UserList,
    UserPublic,
    UserSchemas,
)

# Importa os "moldes" (schemas Pydantic) que validam os dados que entram
# e saem da API.

app = FastAPI()
# Cria a instância principal da aplicação. É ela que "escuta" as rotas
# abaixo e é executada pelo servidor (uvicorn/fastapi dev).


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
# Registra uma rota GET na raiz ("/"). status_code=200 é o padrão de
# sucesso. response_model=Message valida/formata o que a função retorna.
def read_root():
    return {'message': 'Hello World'}
    # Retorna um dicionário simples; o FastAPI converte para JSON
    # automaticamente.


@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
# Rota POST para criar um usuário. status_code=201 (CREATED) é o padrão
# para "recurso criado com sucesso". response_model=UserPublic garante
# que a senha nunca seja devolvida na resposta.
def create_user(user: UserSchemas, session=Depends(get_session)):

    db_user = session.scalar(
        select(User).where(
            or_(User.username == user.username, User.email == user.email)
        )
    )
    # or_() monta um "OU" de verdade no SQL. Usar a palavra-chave "or"
    # do Python aqui não funcionaria: o Python decidiria sozinho qual
    # comparação usar antes mesmo de virar SQL.

    if db_user:
        if db_user.username == user.username or db_user.email == user.email:
            raise HTTPException(
                detail='username/email already exist',
                status_code=HTTPStatus.CONFLICT,
            )

    db_user = User(
        username=user.username,
        email=user.email,
        password=user.password,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@app.get('/users/', status_code=HTTPStatus.OK, response_model=UserList)
# Rota GET que lista todos os usuários cadastrados.
def read_users(limit=10, offset=0, session=Depends(get_session)):
    users = session.scalars(select(User).limit(limit).offset(offset))
    return {'users': users}
    # UserList espera um objeto com a chave "users" contendo uma lista.


@app.put(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
# Rota PUT para atualizar um usuário existente. "{user_id}" é um
# parâmetro de caminho (path parameter) capturado da URL.
def update_user(
    user_id: int, user: UserSchemas, session: Session = Depends(get_session)
):
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='404 - User not found'
        )

    user_db.username = user.username
    user_db.email = user.email
    user_db.password = user.password
    session.add(user_db)

    try:
        session.commit()
        # Só o commit pode falhar aqui: é quando o banco de fato checa
        # a constraint UNIQUE de username/email.
    except IntegrityError:
        raise HTTPException(
            detail='Username or Email already exists',
            status_code=HTTPStatus.CONFLICT,
        )

    session.refresh(user_db)

    return user_db


@app.delete(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=Message
)
# Rota DELETE para remover um usuário pelo id.
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(User).where(User.id == user_id))
    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='404 - User not found'
        )

    session.delete(user_db)
    session.commit()

    return {'message': 'User deleted'}
    # response_model=Message: devolve só uma confirmação, não os dados
    # do usuário apagado.


@app.get('/users/{user_id}', response_model=UserPublic)
# Rota GET para buscar um único usuário específico pelo id.
def read_specific_user(user_id: int, session: Session = Depends(get_session)):
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='404 - User not found'
        )

    return user_db
