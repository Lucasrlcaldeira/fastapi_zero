from http import HTTPStatus

# factory_boy: biblioteca que fabrica objetos de teste em série.
# factory.fuzzy gera valores aleatórios (ex: um estado qualquer).
import factory.fuzzy
import pytest

# DataError: erro que o SQLAlchemy lança quando o banco recusa um valor
# (usado no test_create_todo_error).
from sqlalchemy.exc import DataError

from fastapi_zero.models import Todo, TodoState, User


def test_create_todo(client, token, mock_db_time):
    # Cria uma tarefa pela API, com o token no header (a rota é
    # protegida), e confere o JSON devolvido, incluindo as datas.
    with mock_db_time(model=Todo) as time:
        # mock_db_time (do conftest.py) "congela" o created_at e o
        # updated_at de todo Todo inserido dentro deste "with" numa
        # data fixa. Sem isso, as datas teriam a hora exata em que o
        # teste rodou, e não daria para escrever o valor esperado.
        # "time" é essa data fixa (18/09/2026).
        response = client.post(
            '/todos/',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'title': 'Test todo',
                'description': 'Test todo description',
                'state': 'draft',
            },
        )

    assert response.json() == {
        'id': 1,
        'title': 'Test todo',
        'description': 'Test todo description',
        'state': 'draft',
        'created_at': time.isoformat(),
        'updated_at': time.isoformat(),
    }
    # id=1 porque o banco de teste começa vazio em todo teste.
    # .isoformat() transforma a data no mesmo texto que vem no JSON
    # (ex: "2026-09-18T00:00:00"), para a comparação bater.


class TodoFactory(factory.Factory):
    # "Fábrica" de tarefas: cria objetos Todo com dados inventados, para
    # não precisar escrever title/description na mão em cada teste.
    class Meta:
        model = Todo
        # Diz qual classe a fábrica produz.

    title = factory.Faker('text')
    description = factory.Faker('text')
    # Faker gera textos aleatórios ("Lorem ipsum..." em inglês).
    state = factory.fuzzy.FuzzyChoice(TodoState)
    # Sorteia um dos estados do Enum a cada tarefa criada.
    user_id = 1
    # Valor padrão; os testes trocam pelo id do usuário de verdade.


@pytest.mark.asyncio
async def test_list_todos_should_return_5_todos(session, client, user, token):
    # É async porque salva as tarefas direto no banco, com await.
    expected_todos = 5
    session.add_all(TodoFactory.create_batch(5, user_id=user.id))
    # create_batch(5, ...) fabrica 5 tarefas de uma vez, todas do
    # usuário logado. add_all coloca as 5 na fila da sessão.
    await session.commit()

    response = client.get(
        '/todos/',
        headers={'Authorization': f'Bearer {token}'},
    )
    # Sem filtros na URL: devolve todas (até o limit padrão de 10).

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_pagination_should_return_2_todos(
    session, user, client, token
):
    expected_todos = 2
    session.add_all(TodoFactory.create_batch(5, user_id=user.id))
    await session.commit()

    response = client.get(
        '/todos/?offset=1&limit=2',
        headers={'Authorization': f'Bearer {token}'},
    )
    # Das 5 tarefas: pula 1 (offset) e traz no máximo 2 (limit).

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_title_should_return_5_todos(
    session, user, client, token
):
    expected_todos = 5
    session.add_all(
        TodoFactory.create_batch(5, user_id=user.id, title='Test todo 1')
    )
    # Força o mesmo título nas 5 tarefas, para o filtro achar todas.
    await session.commit()

    response = client.get(
        '/todos/?title=Test todo 1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_description_should_return_5_todos(
    session, user, client, token
):
    expected_todos = 5
    session.add_all(
        TodoFactory.create_batch(5, user_id=user.id, description='description')
    )
    await session.commit()

    response = client.get(
        '/todos/?description=desc',
        headers={'Authorization': f'Bearer {token}'},
    )
    # Busca só "desc" e mesmo assim acha as 5, porque o .contains()
    # da rota procura o texto em QUALQUER parte de "description".

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_state_should_return_5_todos(
    session, user, client, token
):
    expected_todos = 5
    session.add_all(
        TodoFactory.create_batch(5, user_id=user.id, state=TodoState.draft)
    )
    # Sem o state=..., a fábrica SORTEARIA um estado para cada tarefa
    # (FuzzyChoice) e o teste falharia de vez em quando. Fixando
    # TodoState.draft, as 5 tarefas ficam com o mesmo estado.
    await session.commit()

    response = client.get(
        '/todos/?state=draft',
        headers={'Authorization': f'Bearer {token}'},
    )
    # Na URL o estado vai como texto ("draft"); o FilterTodo converte
    # para TodoState.draft. Um valor que não existe no Enum, como
    # ?state=feito, seria recusado com erro 422.

    assert len(response.json()['todos']) == expected_todos
    # As 5 tarefas são "draft", então o filtro deve devolver todas.


@pytest.mark.asyncio
async def test_delete_todo(session, client, user, token):
    todo = TodoFactory(user_id=user.id)
    # Chamar a fábrica direto cria UMA tarefa.

    session.add(todo)
    await session.commit()
    # Depois do commit, o todo.id já está preenchido pelo banco.

    response = client.delete(
        f'/todos/{todo.id}', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Task has been deleted successfully.'
    }


def test_delete_todo_error(client, token):
    # Tenta apagar uma tarefa que não existe (id 10, banco vazio).
    response = client.delete(
        f'/todos/{10}', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


@pytest.mark.asyncio
async def test_delete_other_user_todo(session, client, token, other_user):
    # Teste de SEGURANÇA: a tarefa é do other_user, mas o token é do
    # "user". A API deve se comportar como se a tarefa nem existisse.
    todo_other_user = TodoFactory(user_id=other_user.id)

    session.add(todo_other_user)
    await session.commit()

    response = client.delete(
        f'/todos/{todo_other_user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


def test_patch_todo_error(client, token):
    # PATCH numa tarefa que não existe deve dar 404.
    response = client.patch(
        '/todos/10',
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


@pytest.mark.asyncio
async def test_patch_todo(session, client, user, token):
    todo = TodoFactory(user_id=user.id)

    session.add(todo)
    await session.commit()

    response = client.patch(
        f'/todos/{todo.id}',
        json={'title': 'teste!'},
        headers={'Authorization': f'Bearer {token}'},
    )
    # Manda SÓ o título: o PATCH muda ele e mantém o resto da tarefa.
    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'teste!'


@pytest.mark.asyncio
async def test_create_todo_error(session, user: User):
    # Testa direto no banco (sem a API) o que acontece com um estado
    # que não existe no TodoState.
    todo = Todo(
        title='Test Todo',
        description='Test Desc',
        state='test',
        user_id=user.id,
    )
    # 'test' não é draft, todo, doing, done nem trash. Pela API isso
    # nunca passaria (o Pydantic daria 422), mas aqui não tem Pydantic:
    # o model aceita o texto, e quem decide é o banco.

    session.add(todo)
    # add só coloca na fila (memória); quem fala com o banco é o commit.

    with pytest.raises(DataError):
        await session.commit()
    # No PostgreSQL, a coluna state é um Enum DE VERDADE (o tipo
    # "todostate"), então o próprio banco recusa o valor já na GRAVAÇÃO
    # (no commit), com o erro "invalid input value for enum todostate".
    # (No SQLite era diferente: ele gravava sem reclamar e o erro só
    # aparecia na leitura, como LookupError.)
    # pytest.raises confere que o erro ACONTECE: se o bloco "with"
    # rodar sem erro, o teste é que falha.


def test_list_todos_filter_min_length_exercicio_06(client, token):
    # Exercício: título com menos de 3 letras deve ser recusado.
    tiny_string = 'a'
    response = client.get(
        f'/todos/?title={tiny_string}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    # 422 vem do min_length=3 do FilterTodo (schemas.py): o Pydantic
    # barra o valor antes mesmo de a rota rodar.


def test_list_todos_filter_max_length_exercicio_06(client, token):
    # Exercício: título muito longo (22 letras) também deve ser
    # recusado, o que exige um limite máximo (max_length) no FilterTodo.
    large_string = 'a' * 22
    # 'a' * 22 repete a letra 22 vezes: 'aaaaaaaaaaaaaaaaaaaaaa'.
    response = client.get(
        f'/todos/?title={large_string}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
