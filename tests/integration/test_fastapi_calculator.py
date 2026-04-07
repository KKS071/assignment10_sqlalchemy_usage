# tests/integration/test_fastapi_calculator.py

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    # test client for FastAPI app
    with TestClient(app) as c:
        yield c


def test_add_api(client):
    # test addition endpoint
    response = client.post("/add", json={"a": 10, "b": 5})

    assert response.status_code == 200
    assert response.json()["result"] == 15


def test_subtract_api(client):
    # test subtraction endpoint
    response = client.post("/subtract", json={"a": 10, "b": 5})

    assert response.status_code == 200
    assert response.json()["result"] == 5


def test_multiply_api(client):
    # test multiplication endpoint
    response = client.post("/multiply", json={"a": 10, "b": 5})

    assert response.status_code == 200
    assert response.json()["result"] == 50


def test_divide_api(client):
    # test division endpoint
    response = client.post("/divide", json={"a": 10, "b": 2})

    assert response.status_code == 200
    assert response.json()["result"] == 5


def test_divide_by_zero_api(client):
    # division by zero should return error
    response = client.post("/divide", json={"a": 10, "b": 0})

    assert response.status_code == 400
    assert "error" in response.json()
    assert "Cannot divide by zero!" in response.json()["error"]