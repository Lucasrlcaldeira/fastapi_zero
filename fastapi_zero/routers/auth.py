from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

# select: monta consultas SQL em Python. or_: o "OU" do SQL.
from sqlalchemy import select

# AsyncSession: a versão assíncrona da sessão com o banco. Aqui ela
# serve só para anotar o tipo do parâmetro "session" das rotas.
from sqlalchemy.ext.asyncio import AsyncSession

# get_session: a dependência que abre (e fecha) a sessão com o banco.
from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import (
    Token,
)
from fastapi_zero.security import (
    create_access_token,
    verify_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])

Session = Annotated[AsyncSession, Depends(get_session)]
# Annotated junta o TIPO e a DEPENDÊNCIA num só nome. Assim o parâmetro
# não precisa de "= Depends(...)" e não conta como valor padrão.

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post('/token', response_model=Token)
# Rota de LOGIN. O cliente manda e-mail e senha e, se estiverem certos,
# recebe um token JWT para usar nas rotas protegidas.
async def login_for_access_token(
    form_data: OAuth2Form,
    session: Session,
):
    # "async def": a rota agora é uma corrotina. Enquanto ela espera o
    # banco responder (await), o servidor fica livre para atender
    # outras requisições, em vez de ficar parado esperando.
    # "= Depends()" conta como valor padrão, e parâmetro SEM padrão não pode
    # vir depois de um COM padrão (SyntaxError). Com Annotated, isso some.
    # OAuth2Form: o FastAPI lê o form-data da
    # requisição e monta o objeto com .username e .password.
    user = await session.scalar(
        select(User).where(User.email == form_data.username)
    )
    # await = "espere o banco responder, sem travar o servidor".
    # Toda chamada que vai até o banco (scalar, commit, refresh...)
    # precisa de await; sem ele, "user" seria uma corrotina pendente
    # e não o usuário.
    # O padrão OAuth2 chama o campo de "username", mas aqui o login é
    # feito com o E-MAIL, por isso a busca é por User.email.

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Incorrect email or password',
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Incorrect password'
        )
    # verify_password compara a senha digitada com o hash salvo no
    # banco (o hash não pode ser "desfeito", só comparado).

    access_token = create_access_token({'sub': user.email})
    # "sub" (subject) é o campo padrão do JWT para dizer A QUEM o token
    # pertence. get_current_user lê esse campo depois.
    return {'access_token': access_token, 'token_type': 'Bearer'}
    # "Bearer" = "portador": quem tiver o token em mãos é tratado como
    # o usuário dono dele. Por isso o token nunca deve ser compartilhado.
