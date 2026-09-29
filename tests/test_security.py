from http import HTTPStatus

# decode: usado para "abrir" o token gerado e conferir o conteúdo.
from jwt import decode

from fastapi_zero.security import ALGORITHM, SECRET_KEY, create_access_token


def test_jwt():
    # Testa a função create_access_token diretamente, sem passar pela API.

    data = {'test': 'test'}
    token = create_access_token(data)

    decoded = decode(token, SECRET_KEY, algorithms=ALGORITHM)
    # Decodifica com a mesma chave e o mesmo algoritmo usados para criar.

    assert decoded['test'] == data['test']
    # Os dados que entraram no token precisam sair iguais.
    assert 'exp' in decoded
    # E create_access_token precisa ter adicionado a data de expiração.


def test_jwt_invalid_token(client):
    response = client.delete(
        '/users/1', headers={'Authorization': 'Bearer token-invalido'}
    )
    # Chama uma rota protegida com um token falso. Nem é preciso existir
    # usuário: get_current_user falha antes, ao tentar decodificar.

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
    # 401: o token não passou na validação (DecodeError).


def test_get_current_user_not_found__exercicio(client):
    data = {'no-email': 'test'}
    token = create_access_token(data)
    # Gera um token VÁLIDO (assinado com a SECRET_KEY), mas sem o campo
    # "sub". Ou seja: o decode funciona, só que não diz quem é o dono.

    response = client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )
    # Usa esse token numa rota protegida qualquer (aqui, o DELETE).

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
    # get_current_user cai no "if not subject_email" e devolve 401.


def test_get_current_user_does_not_exists__exercicio(client):
    data = {'sub': 'pedro_h@example.com'}
    token = create_access_token(data)
    # Agora o token é válido E tem "sub", mas aponta para um e-mail que
    # não está cadastrado (o teste nem pede a fixture "user").

    response = client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
    # A busca no banco devolve None, então get_current_user cai no
    # "if not user" e também responde 401. É o caso de um token antigo
    # de uma conta que já foi apagada.
