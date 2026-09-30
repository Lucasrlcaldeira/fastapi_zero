# Usado para criar o "gerenciador de contexto" _mock_db_time (permite
# usar "with mock_db_time(...) as time:" nos testes).
from contextlib import contextmanager

# Tipo usado para representar a data fixa simulada nos testes.
from datetime import datetime

# Framework de testes usado no projeto.
import pytest

# Cliente HTTP de teste do próprio FastAPI — simula requisições sem
# precisar subir um servidor de verdade.
from fastapi.testclient import TestClient

# create_engine: cria a conexão com o banco de dados.
# event: permite "escutar" eventos do SQLAlchemy (usado abaixo para
# interceptar o momento de inserção de um registro).
from sqlalchemy import create_engine, event

# Sessão do SQLAlchemy — é através dela que se conversa com o banco
# (adicionar, consultar, commitar dados).
from sqlalchemy.orm import Session

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


@pytest.fixture
def session():
    # Banco SQLite na memória RAM: rápido e some ao final,
    # então cada teste começa com um banco limpo.
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    # Cria uma "engine" (motor de conexão) para um banco SQLite que
    # existe só na memória RAM, nunca é salvo em disco.

    # Cria no banco todas as tabelas definidas nos seus models.
    table_registry.metadata.create_all(engine)
    # Usa o metadata (definições de tabelas) para criar fisicamente as
    # tabelas nesse banco em memória, antes do teste rodar.

    # Abre uma sessão (a "conversa" com o banco) e fecha sozinha ao terminar.
    with Session(engine) as session:
        # `yield` entrega a sessão ao teste e pausa aqui.
        # Quando o teste acaba, a função continua a partir desta linha.
        yield session
        # Pausa a execução aqui e entrega "session" para o teste usar;
        # quando o teste termina, a execução volta a partir daqui.

    # Limpeza: apaga as tabelas depois do teste.
    table_registry.metadata.drop_all(engine)
    # Remove todas as tabelas, garantindo que o próximo teste comece
    # do zero (isolamento entre testes).


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


@pytest.fixture
def user(session: Session):
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
    session.commit()
    session.refresh(user)

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
