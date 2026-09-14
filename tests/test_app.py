from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.app import app


def test_root_deve_retornar_ola_mundo():
    """
    Esse teste tem 3 etapas (AAA)
    - A: Arrange    - Arranjo
    - A: Act        - Executa a coisa (o SUT)
    - A: Assert     - Garanta que A é A
    :return:
    """
    #Arrenge
    client = TestClient(app)

    #Act
    response = client.get('/')

    #Assert
    assert response.json() == {'message': 'Hello World'}
    assert response.status_code == HTTPStatus.OK
