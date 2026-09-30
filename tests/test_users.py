# Traz os códigos HTTP com nomes legíveis, usados nas asserções abaixo.
from http import HTTPStatus

# Schema usado para montar a resposta esperada a partir do usuário.
from fastapi_zero.schemas import UserPublic


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


def test_read_users(client, user, token):
    # Pede as fixtures "user" (usuário já cadastrado) e "token" (token
    # de login desse usuário), ambas definidas em conftest.py.

    user_schema = UserPublic.model_validate(user).model_dump()
    # model_validate(user) converte o model do SQLAlchemy em UserPublic
    # (possível graças ao from_attributes=True) e model_dump() vira um
    # dicionário: exatamente o formato que a API deve devolver.
    response = client.get(
        '/users/', headers={'Authorization': f'Bearer {token}'}
    )
    # A rota é protegida, então o token vai no header Authorization.

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_update_users(client, user, token):
    response = client.put(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
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


def test_update_integrity_error(client, user, token):
    client.post(
        '/users/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'fausto',
            'email': 'fausto@example.com',
            'password': 'secret',
        },
    )
    # Primeiro cadastra um SEGUNDO usuário, chamado "fausto".

    response = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    # Depois o usuário logado tenta trocar o próprio username para
    # "fausto", que já pertence a outra pessoa.

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username or Email already exists'}
    # O banco recusa (IntegrityError) e a rota devolve 409 (CONFLICT).


def test_delete_users(client, user, token):
    response = client.delete(
        f'/users/{user.id}', headers={'Authorization': f'Bearer {token}'}
    )
    # Remove o usuário de id 1.

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}
    # A rota de delete não devolve os dados do usuário removido, só
    # uma mensagem de confirmação (response_model=Message).


def test_not_found_users(client, user, token):
    response = client.put(
        '/users/2077',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'pedro',
            'email': 'pedro@example.com',
            'password': 'secret',
        },
    )
    # Tenta atualizar um usuário com id diferente do usuário logado (2077).

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}
    # A rota PUT agora exige autenticação e só permite alterar o próprio
    # usuário, então um id diferente retorna 403, não mais 404.


def test_not_delete_users(client, token):
    response = client.delete(
        '/users/2077', headers={'Authorization': f'Bearer {token}'}
    )
    # Tenta remover um usuário com id diferente do usuário logado (2077).
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}
    # A rota DELETE só permite apagar o próprio usuário, então um id
    # diferente retorna 403, não mais 404.


# Exercício do curso: testar a rota GET /users/{user_id}. Os dois testes
# abaixo cobrem o caminho feliz (usuário existe -> 200) e o caminho de
# erro (id inexistente -> 404). Testar os dois lados é o que garante
# que o "if not user_db" da rota realmente funciona.


def test_read_user_exercicio(client, user):
    response = client.get(f'/users/{user.id}')
    # Rota pública: não precisa de token.

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': user.username,
        'email': user.email,
        'id': user.id,
    }


def test_exercicio_not_ok(client):
    # Repare que este teste NÃO pede a fixture "user": o banco começa
    # vazio, então com certeza não existe nenhum usuário de id 77.

    response = client.get('/users/77')
    # Busca um id inexistente. Como a rota é pública, não vai token.

    assert response.status_code == HTTPStatus.NOT_FOUND
    # session.scalar() devolveu None na rota, então ela lança 404.
    assert response.json() == {'detail': '404 - User not found'}
    # O HTTPException coloca a mensagem de erro dentro da chave
    # "detail". O texto precisa ser idêntico ao escrito na rota.


def test_duplicate_create_user(client, user):
    client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    # Cadastra "alice" pela primeira vez (dá certo).

    response = client.post(
        '/users/',
        json={
            'username': 'alice12',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    # Tenta cadastrar outro usuário com o MESMO e-mail. O username é
    # diferente, mas o or_() da rota pega a repetição do e-mail.

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'username/email already exist'}
    # 409 (CONFLICT), com a mesma mensagem definida na rota POST.
