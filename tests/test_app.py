# Traz os códigos HTTP com nomes legíveis, usados nas asserções abaixo.
from http import HTTPStatus


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
