# tests/e2e/test_e2e.py

import pytest


@pytest.mark.e2e
def test_hello_world(page, fastapi_server):
    # homepage should show hello world
    page.goto("http://localhost:8000")

    assert page.inner_text("h1") == "Hello World"


@pytest.mark.e2e
def test_calculator_add(page, fastapi_server):
    # test add operation from UI
    page.goto("http://localhost:8000")

    page.fill("#a", "10")
    page.fill("#b", "5")
    page.click('button:text("Add")')

    assert page.inner_text("#result") == "Result: 15"


@pytest.mark.e2e
def test_calculator_divide_by_zero(page, fastapi_server):
    # divide by zero should show error
    page.goto("http://localhost:8000")

    page.fill("#a", "10")
    page.fill("#b", "0")
    page.click('button:text("Divide")')

    assert page.inner_text("#result") == "Error: Cannot divide by zero!"