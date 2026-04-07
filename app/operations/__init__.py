# app/operations.py

from typing import Union

# Type alias for numbers
Number = Union[int, float]

def add(a: Number, b: Number) -> Number:
    # Return the sum of a and b
    return a + b

def subtract(a: Number, b: Number) -> Number:
    # Return the difference a - b
    return a - b

def multiply(a: Number, b: Number) -> Number:
    # Return the product of a and b
    return a * b

def divide(a: Number, b: Number) -> float:
    # Prevent division by zero
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b