# asyncio: módulo do Python que roda código assíncrono (async/await).
import asyncio

# sys.platform diz em qual sistema operacional o código está rodando
# ('win32' no Windows).
import sys

# HTTPStatus traz os códigos HTTP com nomes legíveis (OK, CREATED,
# NOT_FOUND...) em vez de números "mágicos" como 200, 201, 404.
from http import HTTPStatus

# FastAPI: classe usada para criar a aplicação web.
# HTTPException: usada para interromper uma rota e devolver um erro HTTP.
# Depends: pede ao FastAPI para "injetar" algo pronto no parâmetro da
# rota (ex: uma sessão do banco ou o usuário logado).
from fastapi import FastAPI

from fastapi_zero.routers import auth, todos, users

# Importa os "moldes" (schemas Pydantic) que validam os dados que entram
# e saem da API.
from fastapi_zero.schemas import (
    Message,
)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# No Windows, o loop de eventos padrão (ProactorEventLoop) não funciona
# com o psycopg no modo async. Esta "política" faz o asyncio criar o
# SelectorEventLoop, que é compatível.
# Atenção: isso só vale para quem IMPORTA o app.py (a API). O Alembic
# não importa este arquivo, por isso o migrations/env.py tem a sua
# própria correção.

app = FastAPI()
# Cria a instância principal da aplicação. É ela que "escuta" as rotas
# abaixo e é executada pelo servidor (uvicorn/fastapi dev).

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(todos.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
# Registra uma rota GET na raiz ("/"). status_code=200 é o padrão de
# sucesso. response_model=Message valida/formata o que a função retorna.
async def read_root():
    # Virou "async def" como as outras rotas. Ela não usa await, mas o
    # FastAPI aceita rotas síncronas e assíncronas do mesmo jeito.
    return {'message': 'Hello World'}
    # Retorna um dicionário simples; o FastAPI converte para JSON
    # automaticamente.
