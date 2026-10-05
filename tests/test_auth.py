from http import HTTPStatus

from freezegun import freeze_time


def test_get_token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    # data= (e não json=) envia os campos como formulário, que é o
    # formato que o OAuth2PasswordRequestForm espera. O campo se chama
    # "username", mas recebe o e-mail.

    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token
    # O valor do token muda a cada execução (tem a data de expiração
    # dentro), então o teste só confere que ele existe.


def test_token_expired_after_time(client, user):
    with freeze_time('2026-10-05 15:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )

        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']
        # O JSON de resposta é {'access_token': ..., 'token_type': ...}.
        # No header vai só o access_token, não o dicionário inteiro.

    with freeze_time('2026-10-05 15:31:00'):
        # 31 minutos depois: o token (que dura 30) já expirou.
        response = client.put(
            f'/users/{user.id}',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'username': 'wrongwrong',
                'email': 'wrong@wrong.com',
                'password': 'wrong',
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}
        # Token expirado deve ser recusado com 401.


def test_token_wrong_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'wrong_password'},
    )
    # E-mail certo, senha errada.

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect password'}
    # O usuário existe, mas o verify_password falha: 401.


def test_token_inexistent_user(client):
    response = client.post(
        '/auth/token',
        data={'username': 'no_user@no_domain.com', 'password': 'testtest'},
    )
    # Este teste não pede a fixture "user": o banco está vazio, então
    # nenhum e-mail existe.

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Incorrect email or password'}
    # A busca pelo e-mail não acha ninguém e a rota devolve 404.


def test_refresh_token(client, token):
    response = client.post(
        '/auth/refresh_token',
        headers={'Authorization': f'Bearer {token}'},
    )
    # Manda um token ainda válido (fixture "token") para ser renovado.

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'
    # A rota devolve um token novo no mesmo formato do login.


def test_token_expired_dont_refresh(client, user):
    with freeze_time('2023-07-14 12:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']
        # Gera o token num horário congelado (12:00).

    with freeze_time('2023-07-14 12:31:00'):
        # 31 minutos depois: o token (que dura 30) já expirou.
        response = client.post(
            '/auth/refresh_token',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}
        # Token vencido não pode ser renovado: precisa fazer login de novo.
