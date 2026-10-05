# create_async_engine: cria o "motor" de conexão no modo ASSÍNCRONO.
# AsyncSession: a "conversa" com o banco, mas com métodos que usam
# await (consultar, commitar...) sem travar o servidor.
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi_zero.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL)
# Cria o motor de conexão UMA única vez, quando o módulo é importado,
# usando a URL lida do ".env" (ex: sqlite+aiosqlite:///database.db).
# O "+aiosqlite" escolhe o driver assíncrono do SQLite. O driver
# padrão (sqlite3) é síncrono e não funciona com create_async_engine.


async def get_session():  # pragma: no cover
    # "pragma: no cover" tira esta função do relatório de cobertura: nos
    # testes ela é substituída pela sessão do banco de teste (conftest),
    # então nunca roda e apareceria como linha não testada.

    # Dependência usada pelas rotas com Depends(get_session).
    # Virou "async def" porque abrir e fechar uma sessão assíncrona
    # exige await, e await só pode ser usado dentro de função async.
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # "async with" é o "with" do mundo assíncrono: a sessão é
        # aberta e, no fim, fechada com await por baixo dos panos.
        # expire_on_commit=False: por padrão, depois do commit o
        # SQLAlchemy "esquece" os valores dos objetos e os relê do
        # banco no próximo acesso (ex: user.email). No modo async essa
        # releitura escondida não é possível (ela precisaria de um
        # await), então desligamos esse comportamento.
        yield session
        # yield entrega a sessão para a rota e pausa aqui. Quando a
        # requisição termina, o "async with" fecha a sessão sozinho.
        # Nos testes, essa função é trocada por outra (veja
        # app.dependency_overrides em tests/conftest.py).
