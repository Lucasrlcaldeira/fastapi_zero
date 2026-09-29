# create_engine: cria o "motor" que sabe como se conectar ao banco.
from sqlalchemy import create_engine

# Session: a "conversa" com o banco (consultar, adicionar, commitar).
from sqlalchemy.orm import Session

from fastapi_zero.settings import Settings

engine = create_engine(Settings().DATABASE_URL)
# Cria o motor de conexão UMA única vez, quando o módulo é importado,
# usando a URL lida do ".env" (ex: sqlite:///database.db).


def get_session():
    # Dependência usada pelas rotas com Depends(get_session).
    with Session(engine) as session:
        yield session
        # yield entrega a sessão para a rota e pausa aqui. Quando a
        # requisição termina, o "with" fecha a sessão automaticamente.
        # Nos testes, essa função é trocada por outra (veja
        # app.dependency_overrides em tests/conftest.py).
