# asdict converte uma instância de dataclass (como User, veja
# models.py) num dicionário comum, facilitando a comparação no assert.
from dataclasses import asdict

# pytest: usado aqui para a marca @pytest.mark.asyncio.
import pytest

# select é usado para montar a consulta (query) que busca o usuário no
# banco.
from sqlalchemy import select

# AsyncSession: usado só para anotar o tipo da fixture "session".
from sqlalchemy.ext.asyncio import AsyncSession

# Model que será testado diretamente contra o banco.
from fastapi_zero.models import User


@pytest.mark.asyncio
# Marca o teste como assíncrono: o pytest-asyncio cria um "loop de
# eventos" e roda o teste nele, permitindo usar await lá dentro.
async def test_create_user(session: AsyncSession, mock_db_time):
    # "session" e "mock_db_time" são fixtures injetadas automaticamente
    # (definidas em conftest.py).

    with mock_db_time(model=User) as time:
        # Enquanto este bloco roda, qualquer User inserido terá seu
        # created_at e updated_at fixados na data retornada em "time",
        # em vez da data real do sistema.
        new_user = User(username='test', email='test@test', password='secret')
        # Cria uma instância de User em memória (ainda não salva no
        # banco). Note que id, created_at e updated_at não são
        # passados, pois têm init=False em models.py.

        session.add(new_user)
        # Marca o objeto para ser inserido no banco (ainda não grava
        # de fato).
        await session.commit()
        # Confirma a transação, gravando o usuário no banco de
        # verdade (o banco em memória criado pela fixture "session").
        # Leva await porque conversa com o banco.

        user = await session.scalar(
            select(User).where(User.username == 'test')
        )
        # Consulta o banco buscando o usuário pelo username, para
        # conferir que ele foi realmente salvo (e não só ficou no
        # objeto Python original).

    assert asdict(user) == {
        'id': 1,
        'username': 'test',
        'email': 'test@test',
        'password': 'secret',
        'created_at': time,
        'updated_at': time,
        'todos': [],
    }
    # Confere se todos os campos do usuário salvo batem com o
    # esperado, incluindo a data fixa simulada por mock_db_time.
    # "todos" vem do relationship em models.py: um usuário recém-criado
    # ainda não tem tarefas, então a lista é vazia.
