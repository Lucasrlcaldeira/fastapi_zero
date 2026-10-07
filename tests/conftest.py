# Usado para criar o "gerenciador de contexto" _mock_db_time (permite
# usar "with mock_db_time(...) as time:" nos testes).
from contextlib import contextmanager

# Tipo usado para representar a data fixa simulada nos testes.
from datetime import datetime

# factory_boy: gera objetos de teste (aqui, Users) com dados
# automáticos, sem precisar escrever username/email na mão.
import factory

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

# testcontainers: sobe um container Docker DESCARTÁVEL (aqui, um
# PostgreSQL) só para os testes, e o apaga no final. Assim os testes
# usam o mesmo banco da aplicação, sem tocar nos dados de verdade.
from testcontainers.postgres import PostgresContainer

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
        # Devolve a sessão do banco DE TESTE (o Postgres descartável do
        # testcontainers), em vez da sessão do banco real (app_db).

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        # "Troca a peça": toda rota que pedir Depends(get_session)
        # vai receber get_session_override() no lugar. Assim os testes
        # nunca mexem no banco de verdade.
        yield client

    app.dependency_overrides.clear()
    # Desfaz a troca depois do teste, para não afetar outros testes.


@pytest.fixture(scope='session')
# scope='session': esta fixture roda UMA vez só, para a execução
# inteira do pytest (não tem nada a ver com a AsyncSession do
# SQLAlchemy). Subir um container leva segundos; se fosse por teste,
# cada um esperaria o Postgres ligar de novo.
def engine():
    with PostgresContainer('postgres:18.6', driver='psycopg') as postgres:
        # Liga um Postgres 18.6 descartável no Docker (o Docker Desktop
        # precisa estar aberto). Ao sair do "with", ele é apagado.
        # driver='psycopg': monta a URL de conexão com o driver psycopg.
        yield create_async_engine(postgres.get_connection_url())
        # Entrega aos testes um engine apontando para esse container.


@pytest_asyncio.fixture
# Fixture assíncrona usa o decorador do pytest_asyncio: o
# @pytest.fixture comum não sabe "esperar" (await) uma função async.
async def session(engine):
    # Pede o "engine" acima: o container é o mesmo para todos os testes,
    # mas cada teste ganha tabelas novinhas (create_all/drop_all).
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

    user = UserFactory(password=get_password_hash(password))

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


@pytest_asyncio.fixture
# Também é async, porque salva o usuário no banco com await.
async def other_user(session: AsyncSession):
    # Cria um SEGUNDO usuário, diferente do "user". Serve para testar o
    # que acontece quando o usuário logado mexe em dados de outra
    # pessoa (403) ou tenta usar um username/e-mail que já é dela (409).
    # Como os dois usam a UserFactory, cada um ganha um username único.
    password = 'testtest'

    user = UserFactory(password=get_password_hash(password))

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
    # Dá aos testes acesso às configurações (SECRET_KEY, ALGORITHM...),
    # as mesmas lidas do .env pela aplicação.


class UserFactory(factory.Factory):
    # "Fábrica" de Users para os testes: cada chamada a UserFactory()
    # devolve um User novo (ainda não salvo no banco) com dados prontos.
    class Meta:
        model = User
        # Diz à factory qual classe ela deve instanciar.

    username = factory.sequence(lambda n: f'test{n}')
    # sequence: cada usuário criado recebe um número diferente
    # (test0, test1, test2...), então nunca há username repetido.
    email = factory.lazy_attribute(lambda obj: f'{obj.username}@test.com')
    # lazy_attribute: calculado na hora, a partir dos outros campos.
    # Assim o e-mail acompanha o username (test1 -> test1@test.com).
    password = factory.lazy_attribute(
        lambda obj: f'{obj.username}&1ha412asrf5'
    )
    # Senha padrão; as fixtures sobrescrevem com o hash de 'testtest'.
