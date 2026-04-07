# tests/unit/test_calculator.py

import pytest
from typing import Union
from app.operations import add, subtract, multiply, divide

Number = Union[int, float]


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (2, 3, 5),
        (-2, -3, -5),
        (2.5, 3.5, 6.0),
        (-2.5, 3.5, 1.0),
        (0, 0, 0),
    ],
)
def test_add(a: Number, b: Number, expected: Number):
    # test add function
    assert add(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (5, 3, 2),
        (-5, -3, -2),
        (5.5, 2.5, 3.0),
        (-5.5, -2.5, -3.0),
        (0, 0, 0),
    ],
)
def test_subtract(a: Number, b: Number, expected: Number):
    # test subtract function
    assert subtract(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (2, 3, 6),
        (-2, 3, -6),
        (2.5, 4.0, 10.0),
        (-2.5, 4.0, -10.0),
        (0, 5, 0),
    ],
)
def test_multiply(a: Number, b: Number, expected: Number):
    # test multiply function
    assert multiply(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (6, 3, 2.0),
        (-6, 3, -2.0),
        (6.0, 3.0, 2.0),
        (-6.0, 3.0, -2.0),
        (0, 5, 0.0),
    ],
)
def test_divide(a: Number, b: Number, expected: float):
    # test divide function
    assert divide(a, b) == expected


def test_divide_by_zero():
    # divide by zero should raise error
    with pytest.raises(ValueError) as exc:
        divide(6, 0)

    assert "Cannot divide by zero!" in str(exc.value)