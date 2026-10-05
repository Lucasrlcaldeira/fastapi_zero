# HTTPStatus traz os códigos HTTP com nomes legíveis (OK, CREATED,
# NOT_FOUND...) em vez de números "mágicos" como 200, 201, 404.
from http import HTTPStatus

# FastAPI: classe usada para criar a aplicação web.
# HTTPException: usada para interromper uma rota e devolver um erro HTTP.
# Depends: pede ao FastAPI para "injetar" algo pronto no parâmetro da
# rota (ex: uma sessão do banco ou o usuário logado).
from fastapi import FastAPI

from fastapi_zero.routers import auth, users

# Importa os "moldes" (schemas Pydantic) que validam os dados que entram
# e saem da API.
from fastapi_zero.schemas import (
    Message,
)

app = FastAPI()
# Cria a instância principal da aplicação. É ela que "escuta" as rotas
# abaixo e é executada pelo servidor (uvicorn/fastapi dev).

app.include_router(auth.router)
app.include_router(users.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
# Registra uma rota GET na raiz ("/"). status_code=200 é o padrão de
# sucesso. response_model=Message valida/formata o que a função retorna.
async def read_root():
    # Virou "async def" como as outras rotas. Ela não usa await, mas o
    # FastAPI aceita rotas síncronas e assíncronas do mesmo jeito.
    return {'message': 'Hello World'}
    # Retorna um dicionário simples; o FastAPI converte para JSON
    # automaticamente.
