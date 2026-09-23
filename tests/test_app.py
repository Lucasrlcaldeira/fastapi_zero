from http import HTTPStatus

# Traz os códigos HTTP com nomes legíveis, usados nas asserções abaixo.
from fastapi_zero.schemas import UserPublic


def test_root_deve_retornar_ola_mundo(client):
    # "client" é injetado automaticamente pela fixture definida em
    # conftest.py.
    response = client.get('/')
    # Simula uma requisição GET para a rota raiz.

    # Assert
    assert response.json() == {'message': 'Hello World'}
    # Confere se o corpo da resposta é exatamente o esperado.
    assert response.status_code == HTTPStatus.OK
    # Confere se o status HTTP retornado foi 200 (OK).


def test_client_user(client):
    response = client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    # Envia um POST simulando a criação de um usuário, com corpo JSON.

    assert response.status_code == HTTPStatus.CREATED
    # Espera-se status 201 (recurso criado).
    assert response.json() == {
        'id': 1,
        'username': 'alice',
        'email': 'alice@example.com',
    }
    # A resposta não deve conter "password" (protegido por UserPublic).


def test_read_users(client):
    response = client.get('/users/')
    # Cada teste recebe um banco em memória próprio e isolado (fixture
    # "session"), então aqui a listagem começa vazia.

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}
    # Confere se a listagem de um banco vazio retorna uma lista vazia.


def test_read_users_with_users(client, user):

    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_update_users(client, user):
    response = client.put(
        '/users/1',
        json={
            'username': 'pedro',
            'email': 'pedro@example.com',
            'password': 'secret',
        },
    )
    # Atualiza o usuário de id 1 com novos dados.

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'pedro',
        'email': 'pedro@example.com',
        'id': 1,
    }
    # A resposta deve refletir os dados novos.


def test_update_integrity_error(client, user):
    client.post(
        '/users/',
        json={
            'username': 'fausto',
            'email': 'fausto@example.com',
            'password': 'secret',
        },
    )

    response = client.put(
        f'/users/{user.id}',
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username or Email already exists'}


def test_delete_users(client, user):
    response = client.delete('/users/1')
    # Remove o usuário de id 1.

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}
    # A rota de delete não devolve os dados do usuário removido, só
    # uma mensagem de confirmação (response_model=Message).


def test_not_found_users(client):
    response = client.put(
        '/users/2077',
        json={
            'username': 'pedro',
            'email': 'pedro@example.com',
            'password': 'secret',
        },
    )
    # Tenta atualizar um usuário com id que não existe (2077).

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': '404 - User not found'}
    # Espera-se erro 404, com a mensagem definida em app.py.


def test_not_delete_users(client):
    response = client.delete('/users/2077')
    # Tenta remover um usuário inexistente.
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': '404 - User not found'}


# Exercício do curso: testar a rota GET /users/{user_id}. O caso de
# sucesso abaixo já está implementado; o caso de erro (id inexistente)
# segue comentado como pendência.


def test_read_user_exercicio(client, user):
    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': user.username,
        'email': user.email,
        'id': user.id,
    }


"""def test_exercicio_not_ok(client):
    response = client.get('/users/77')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': '404 - User not found'}"""


def test_duplicate_create_user(client, user):
    client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )

    response = client.post(
        '/users/',
        json={
            'username': 'alice12',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'username/email already exist'}
