from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

# select: monta consultas SQL em Python. or_: o "OU" do SQL.
from sqlalchemy import or_, select

# Erro que o banco lança quando uma constraint é violada (ex: tentar
# salvar um username que já existe numa coluna unique=True).
from sqlalchemy.exc import IntegrityError

# AsyncSession: a versão assíncrona da sessão com o banco. Aqui ela
# serve só para anotar o tipo do parâmetro "session" das rotas.
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.database import get_session
from fastapi_zero.models import User

# Importa os "moldes" (schemas Pydantic) que validam os dados que entram
# e saem da API.
from fastapi_zero.schemas import (
    FilterPage,
    Message,
    UserList,
    UserPublic,
    UserSchemas,
)
from fastapi_zero.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix='/users', tags=['users'])

Session = Annotated[AsyncSession, Depends(get_session)]
# Mesmo atalho do auth.py, agora apontando para a sessão assíncrona.

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
# Rota POST para criar um usuário. status_code=201 (CREATED) é o padrão
# para "recurso criado com sucesso". response_model=UserPublic garante
# que a senha nunca seja devolvida na resposta.
async def create_user(user: UserSchemas, session: Session):
    # session=Depends(get_session): a cada requisição o FastAPI chama
    # get_session() e entrega aqui uma sessão aberta com o banco.
    # A rota é "async def" porque usa await nas chamadas ao banco.

    db_user = await session.scalar(
        select(User).where(
            or_(User.username == user.username, User.email == user.email)
        )
    )
    # or_() monta um "OU" de verdade no SQL. Usar a palavra-chave "or"
    # do Python aqui não funcionaria: o Python decidiria sozinho qual
    # comparação usar antes mesmo de virar SQL.
    # session.scalar() devolve o primeiro resultado encontrado, ou None.
    # O await faz a rota esperar a resposta do banco sem travar o
    # servidor para as outras requisições.

    if db_user:
        if db_user.username == user.username or db_user.email == user.email:
            raise HTTPException(
                detail='username/email already exist',
                status_code=HTTPStatus.CONFLICT,
            )
            # 409 (CONFLICT): o pedido é válido, mas bate de frente com
            # um dado que já existe no banco.

    db_user = User(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
    )
    # Monta o objeto User em memória. A senha é guardada como HASH
    # (uma "impressão digital" irreversível), nunca como texto puro.

    session.add(db_user)
    # Coloca o objeto na "fila" da sessão (ainda não grava no banco).
    # Repare: add() NÃO tem await, porque só mexe na memória. Só leva
    # await o que de fato conversa com o banco (commit, refresh...).
    await session.commit()
    # Confirma a transação: agora sim o INSERT acontece no banco.
    await session.refresh(db_user)
    # Relê o registro do banco para preencher os campos que o próprio
    # banco gerou (id, created_at, updated_at).

    return db_user
    # Devolve o model User; o response_model=UserPublic filtra os campos
    # e descarta a senha antes de virar JSON.


@router.get('/', status_code=HTTPStatus.OK, response_model=UserList)
# Rota GET que lista todos os usuários cadastrados.
async def read_users(
    session: Session,
    current_user: CurrentUser,
    filter_users: Annotated[FilterPage, Query()],
):

    users = await session.scalars(
        select(User).limit(filter_users.limit).offset(filter_users.offset)
    )
    # session.scalars() (no plural) devolve TODOS os resultados da
    # consulta, não só o primeiro.
    return {'users': users}
    # UserList espera um objeto com a chave "users" contendo uma lista.


@router.put('/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic)
# Rota PUT para atualizar um usuário existente. "{user_id}" é um
# parâmetro de caminho (path parameter) capturado da URL.
async def update_user(
    user_id: int,
    user: UserSchemas,
    session: Session,
    current_user: CurrentUser,
):

    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )
    # Regra de autorização: cada usuário só pode alterar a si mesmo.
    # 403 (FORBIDDEN) = "sei quem você é, mas você não pode fazer isso".
    # É diferente do 401, que é "não sei quem você é".

    current_user.username = user.username
    current_user.email = user.email
    current_user.password = get_password_hash(user.password)
    # Como current_user já veio do banco, basta alterar os atributos:
    # o SQLAlchemy percebe as mudanças e gera um UPDATE no commit.
    session.add(current_user)

    try:
        await session.commit()
        # Só o commit pode falhar aqui: é quando o banco de fato checa
        # a constraint UNIQUE de username/email.
    except IntegrityError:
        raise HTTPException(
            detail='Username or Email already exists',
            status_code=HTTPStatus.CONFLICT,
        )

    await session.refresh(current_user)
    # Relê do banco para pegar valores atualizados por ele (ex:
    # updated_at, que usa onupdate=func.now() no model).

    return current_user


@router.delete('/{user_id}', status_code=HTTPStatus.OK, response_model=Message)
# Rota DELETE para remover um usuário pelo id.
async def delete_user(
    user_id: int,
    session: Session,
    current_user: CurrentUser,
):

    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )
    # Mesma regra do PUT: só é possível apagar a própria conta.

    await session.delete(current_user)
    await session.commit()
    # delete() marca o registro para remoção; o commit executa o DELETE.
    # Diferente do add(), na AsyncSession o delete() leva await: ele
    # pode precisar ir ao banco carregar dados ligados ao registro.

    return {'message': 'User deleted'}
    # response_model=Message: devolve só uma confirmação, não os dados
    # do usuário apagado.


@router.get('/{user_id}', response_model=UserPublic)
# Rota GET para buscar um único usuário específico pelo id.
# Repare que ela NÃO pede get_current_user: é uma rota pública.
async def read_specific_user(user_id: int, session: Session):
    user_db = await session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='404 - User not found'
        )
    # scalar() devolve None quando não acha nada; nesse caso, 404.

    return user_db
