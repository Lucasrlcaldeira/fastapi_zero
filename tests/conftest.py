# Usado para criar o "gerenciador de contexto" _mock_db_time (permite
# usar "with mock_db_time(...) as time:" nos testes).
from contextlib import contextmanager

# Tipo usado para representar a data fixa simulada nos testes.
from datetime import datetime

# Framework de testes usado no projeto.
import pytest

# pytest_asyncio: plugin que ensina o pytest a rodar fixtures e
# testes assíncronos (async def), que usam await.
import pytest_asyncio

# Cliente HTTP de teste do próprio FastAPI — simula requisições sem
# precisar subir um servidor de verdade.
from fastapi.testclient import TestClient

# event: permite "escutar" eventos do SQLAlchemy (usado abaixo para
# interceptar o momento de inserção de um registro).
from sqlalchemy import event

# AsyncSession: sessão assíncrona do SQLAlchemy — é através dela que
# se conversa com o banco (adicionar, consultar, commitar dados).
# create_async_engine: cria a conexão com o banco no modo assíncrono.
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# StaticPool: faz todas as conexões reaproveitarem a MESMA conexão.
# Necessário com SQLite em memória: cada conexão nova teria um banco
# vazio diferente, e o teste "perderia" as tabelas criadas.
from sqlalchemy.pool import StaticPool

# Importa a aplicação FastAPI já configurada, para testá-la.
from fastapi_zero.app import app

# A dependência original de sessão, que será trocada nos testes.
from fastapi_zero.database import get_session

# User e o "catálogo" de tabelas, para poder criá-las/apagá-las nos
# testes.
from fastapi_zero.models import User, table_registry
from fastapi_zero.security import get_password_hash
from fastapi_zero.settings import Settings


# Fixture = "preparação" que o pytest entrega pronta para os testes.
# Basta o teste pedir `client` como parâmetro que o pytest injeta o retorno.
@pytest.fixture
# Decorador que transforma a função abaixo numa fixture reutilizável
# pelos testes.
def client(session):
    # Cliente de teste: simula requisições HTTP (get, post...) na sua API
    # sem precisar subir um servidor de verdade.
    # Ela pede a fixture "session" como parâmetro: uma fixture pode
    # depender de outra, e o pytest resolve a ordem sozinho.
    def get_session_override():
        return session
        # Devolve a sessão do banco EM MEMÓRIA do teste, em vez da
        # sessão do banco real (database.db).

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        # "Troca a peça": toda rota que pedir Depends(get_session)
        # vai receber get_session_override() no lugar. Assim os testes
        # nunca mexem no banco de verdade.
        yield client

    app.dependency_overrides.clear()
    # Desfaz a troca depois do teste, para não afetar outros testes.


@pytest_asyncio.fixture
# Fixture assíncrona usa o decorador do pytest_asyncio: o
# @pytest.fixture comum não sabe "esperar" (await) uma função async.
async def session():
    # Banco SQLite na memória RAM: rápido e some ao final,
    # então cada teste começa com um banco limpo.
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    # Cria uma "engine" (motor de conexão) para um banco SQLite que
    # existe só na memória RAM, nunca é salvo em disco.
    # "sqlite+aiosqlite" usa o driver assíncrono aiosqlite, o mesmo
    # tipo de driver usado pela aplicação de verdade.

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
    # Cria no banco todas as tabelas definidas nos models, antes do
    # teste rodar. engine.begin() abre uma conexão com transação.
    # create_all é uma função SÍNCRONA, então run_sync() a executa
    # "por dentro" da conexão assíncrona.

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # expire_on_commit=False: mantém os valores dos objetos depois
        # do commit (veja a explicação em database.py).
        # `yield` entrega a sessão ao teste e pausa aqui.
        # Quando o teste acaba, a função continua a partir desta linha.
        yield session
        # Pausa a execução aqui e entrega "session" para o teste usar;
        # quando o teste termina, a execução volta a partir daqui.

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)
    # Limpeza: apaga as tabelas depois do teste, garantindo que o
    # próximo comece do zero (isolamento entre testes).


@contextmanager
# Transforma a função abaixo num gerenciador de contexto, usável com
# "with _mock_db_time(...) as time:".
def _mock_db_time(model, time=datetime(2026, 9, 18)):
    # Recebe qual model "vigiar" e qual data/hora fixa usar (padrão:
    # 18/09/2026).
    def fake_time_hook(mapper, connection, target):
        # Função que será chamada automaticamente pelo SQLAlchemy
        # antes de cada INSERT.
        if hasattr(target, 'created_at'):
            # Só mexe no objeto se ele tiver o campo created_at.
            target.created_at = time
            # Sobrescreve a data real pela data fixa combinada.

        if hasattr(target, 'updated_at'):
            target.updated_at = time

    event.listen(model, 'before_insert', fake_time_hook)
    # Registra fake_time_hook para rodar sempre que o model informado
    # for inserido no banco (evento "before_insert").

    yield time
    # Entrega a data fixa para quem usou o "with", pausando aqui até o
    # bloco "with" terminar.

    event.remove(model, 'before_insert', fake_time_hook)
    # Remove o "escutador" de evento depois do uso, para não afetar
    # outros testes.


@pytest.fixture
def mock_db_time():
    return _mock_db_time
    # Expõe a função _mock_db_time como fixture, para os testes
    # poderem chamá-la com "mock_db_time(model=User)".


@pytest_asyncio.fixture
# Também é async, porque salva o usuário no banco com await.
async def user(session: AsyncSession):
    # Cria um usuário já salvo no banco de teste, para os testes que
    # precisam de alguém cadastrado (ex: login, update, delete).
    password = 'testtest'
    user = User(
        username='Teste',
        email='test@test.com',
        password=get_password_hash(password),
    )
    # A senha é salva como hash, igual à rota de criação faz.
    session.add(user)
    await session.commit()
    await session.refresh(user)
    # commit grava no banco; refresh relê o registro para preencher
    # o id e as datas. Os dois vão ao banco, por isso levam await.

    user.clean_password = password
    # "Pendura" a senha original (texto puro) no objeto. Ela não é
    # coluna do banco, só um atributo extra para os testes conseguirem
    # fazer login, já que o hash não pode ser revertido.
    return user


@pytest.fixture
def token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    return response.json()['access_token']
    # Faz login com o usuário de teste e devolve o token JWT, para os
    # testes de rotas protegidas mandarem no header Authorization.


@pytest.fixture
def settings():
    return Settings()
