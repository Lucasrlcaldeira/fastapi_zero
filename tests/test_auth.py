from http import HTTPStatus


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
