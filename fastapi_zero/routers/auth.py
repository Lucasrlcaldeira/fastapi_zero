from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

# select: monta consultas SQL em Python. or_: o "OU" do SQL.
from sqlalchemy import select

# Tipo da sessão do banco, usado só para anotar os parâmetros das rotas.
from sqlalchemy.orm import Session

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

Session = Annotated[Session, Depends(get_session)]
# Annotated junta o TIPO e a DEPENDÊNCIA num só nome. Assim o parâmetro
# não precisa de "= Depends(...)" e não conta como valor padrão.

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post('/token', response_model=Token)
# Rota de LOGIN. O cliente manda e-mail e senha e, se estiverem certos,
# recebe um token JWT para usar nas rotas protegidas.
def login_for_access_token(
    form_data: OAuth2Form,
    session: Session,
):
    # "= Depends()" conta como valor padrão, e parâmetro SEM padrão não pode
    # vir depois de um COM padrão (SyntaxError). Com Annotated, isso some.
    # OAuth2Form: o FastAPI lê o form-data da
    # requisição e monta o objeto com .username e .password.
    user = session.scalar(select(User).where(User.email == form_data.username))
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
