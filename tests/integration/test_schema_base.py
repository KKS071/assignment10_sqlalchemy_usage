# tests/integration/test_schema_base.py

import pytest
from pydantic import ValidationError
from app.schemas.base import UserBase, PasswordMixin, UserCreate, UserLogin


def test_user_base_valid():
    # valid user base data
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
    }

    user = UserBase(**data)

    assert user.first_name == "John"
    assert user.email == "john.doe@example.com"


def test_user_base_invalid_email():
    # invalid email should fail
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "invalid-email",
        "username": "johndoe",
    }

    with pytest.raises(ValidationError):
        UserBase(**data)


def test_password_mixin_valid():
    # valid password
    data = {"password": "SecurePass123"}

    obj = PasswordMixin(**data)

    assert obj.password == "SecurePass123"


def test_password_mixin_invalid_short_password():
    # too short password
    data = {"password": "short"}

    with pytest.raises(ValidationError):
        PasswordMixin(**data)


def test_password_mixin_no_uppercase():
    # missing uppercase letter
    data = {"password": "lowercase1"}

    with pytest.raises(ValidationError, match="Password must contain at least one uppercase letter"):
        PasswordMixin(**data)


def test_password_mixin_no_lowercase():
    # missing lowercase letter
    data = {"password": "UPPERCASE1"}

    with pytest.raises(ValidationError, match="Password must contain at least one lowercase letter"):
        PasswordMixin(**data)


def test_password_mixin_no_digit():
    # missing number
    data = {"password": "NoDigitsHere"}

    with pytest.raises(ValidationError, match="Password must contain at least one digit"):
        PasswordMixin(**data)


def test_user_create_valid():
    # valid user creation schema
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SecurePass123",
    }

    user = UserCreate(**data)

    assert user.username == "johndoe"
    assert user.password == "SecurePass123"


def test_user_create_invalid_password():
    # invalid password in create schema
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "short",
    }

    with pytest.raises(ValidationError):
        UserCreate(**data)


def test_user_login_valid():
    # valid login data
    data = {"username": "johndoe", "password": "SecurePass123"}

    user = UserLogin(**data)

    assert user.username == "johndoe"


def test_user_login_invalid_username():
    # username too short
    data = {"username": "jd", "password": "SecurePass123"}

    with pytest.raises(ValidationError):
        UserLogin(**data)


def test_user_login_invalid_password():
    # invalid password
    data = {"username": "johndoe", "password": "short"}

    with pytest.raises(ValidationError):
        UserLogin(**data)