# datetime/timedelta: usados para calcular quando o token expira.
from datetime import datetime, timedelta
from http import HTTPStatus

# ZoneInfo: fuso horário. O JWT usa horários em UTC.
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException

# OAuth2PasswordBearer: sabe extrair o token do header
# "Authorization: Bearer <token>" das requisições.
from fastapi.security import OAuth2PasswordBearer

# encode: cria (assina) um token JWT. decode: lê e valida um token.
# DecodeError: erro lançado quando o token é inválido ou foi adulterado.
from jwt import DecodeError, decode, encode

# PasswordHash: biblioteca que gera e confere hashes de senha.
from pwdlib import PasswordHash
from sqlalchemy import select

# AsyncSession: tipo da sessão assíncrona com o banco.
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.settings import Settings

settings = Settings()

pwd_context = PasswordHash.recommended()
# Cria o "gerador de hash" com o algoritmo recomendado pela pwdlib
# (Argon2, instalado via pwdlib[argon2]).


def get_password_hash(password: str):
    return pwd_context.hash(password)
    # Transforma a senha em um hash. O mesmo texto gera hashes diferentes
    # a cada chamada (por causa do "salt" aleatório), e não dá para
    # voltar do hash para a senha original.


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)
    # Confere se a senha digitada (texto puro) corresponde ao hash salvo
    # no banco. Devolve True ou False.


def create_access_token(data: dict):
    to_encode = data.copy()
    # Copia o dicionário para não alterar o original de quem chamou.

    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    # Momento exato em que o token deixa de valer: agora + 30 minutos.

    to_encode.update({'exp': expire})
    # "exp" é um campo padrão do JWT. A biblioteca jwt checa sozinha se
    # o token já expirou ao fazer o decode.

    encode_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    # Gera o token: um texto em 3 partes (cabeçalho.dados.assinatura).
    # Os dados NÃO são criptografados (qualquer um consegue ler), mas a
    # assinatura impede que alguém os altere sem a SECRET_KEY.

    return encode_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')
# Diz ao FastAPI que o token é obtido na rota "/token". Isso também faz
# aparecer o botão "Authorize" na documentação automática (/docs).


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    # Dependência usada pelas rotas protegidas. Ela recebe o token do
    # header, valida e devolve o User dono dele.
    # Uma dependência pode depender de outras: aqui ela mesma pede a
    # sessão do banco e o token.
    # Ela também virou "async def", porque busca o usuário no banco
    # com await. O FastAPI sabe chamar dependências síncronas e
    # assíncronas, então as rotas continuam usando do mesmo jeito.
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    # Erro 401 criado uma vez e reaproveitado em todos os casos de
    # falha abaixo. O header WWW-Authenticate avisa o cliente de que
    # ele precisa se autenticar com um token Bearer.

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
        )
        # Confere a assinatura e a validade do token e devolve os dados
        # que foram guardados nele (o "payload").
        # Atenção: no decode é "algorithms" (plural, uma LISTA dos
        # algoritmos aceitos); no encode é "algorithm" (singular). Com o
        # nome errado, o PyJWT lança DecodeError e toda rota protegida
        # devolve 401.
        subject_email = payload.get('sub')
        # Pega o dono do token (colocado como "sub" no login).

        if not subject_email:
            raise credentials_exception

    except DecodeError:
        raise credentials_exception
        # Token malformado ou com assinatura inválida.

    user = await session.scalar(
        select(User).where(User.email == subject_email)
    )
    # O token é válido, mas o usuário ainda existe? (ele pode ter sido
    # apagado depois que o token foi gerado).

    if not user:
        raise credentials_exception

    return user
    # Esse User é o que chega nas rotas como "current_user".
