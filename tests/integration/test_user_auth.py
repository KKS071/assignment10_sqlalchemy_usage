# tests/integration/test_user_auth.py

import pytest
from app.models.user import User


def test_password_hashing(db_session, fake_user_data):
    # check hashing + verification
    password = "TestPass123"
    hashed = User.hash_password(password)

    user = User(
        first_name=fake_user_data["first_name"],
        last_name=fake_user_data["last_name"],
        email=fake_user_data["email"],
        username=fake_user_data["username"],
        password=hashed,
    )

    assert user.verify_password(password) is True
    assert user.verify_password("WrongPass123") is False
    assert hashed != password


def test_user_registration(db_session, fake_user_data):
    # basic registration flow
    fake_user_data["password"] = "TestPass123"

    user = User.register(db_session, fake_user_data)
    db_session.commit()

    assert user.first_name == fake_user_data["first_name"]
    assert user.last_name == fake_user_data["last_name"]
    assert user.email == fake_user_data["email"]
    assert user.username == fake_user_data["username"]
    assert user.is_active is True
    assert user.is_verified is False
    assert user.verify_password("TestPass123") is True


def test_duplicate_user_registration(db_session):
    # duplicate email should fail
    user1 = {
        "first_name": "Test",
        "last_name": "User1",
        "email": "unique.test@example.com",
        "username": "uniqueuser1",
        "password": "TestPass123",
    }

    user2 = {
        "first_name": "Test",
        "last_name": "User2",
        "email": "unique.test@example.com",  # same email
        "username": "uniqueuser2",
        "password": "TestPass123",
    }

    first_user = User.register(db_session, user1)
    db_session.commit()
    db_session.refresh(first_user)

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, user2)


def test_user_authentication(db_session, fake_user_data):
    # login should return token + user
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(
        db_session,
        fake_user_data["username"],
        "TestPass123",
    )

    assert result is not None
    assert "access_token" in result
    assert "token_type" in result
    assert result["token_type"] == "bearer"
    assert "user" in result


def test_user_last_login_update(db_session, fake_user_data):
    # last_login should update after auth
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()

    assert user.last_login is None

    User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    db_session.refresh(user)

    assert user.last_login is not None


def test_unique_email_username(db_session):
    # uniqueness constraint check
    user1 = {
        "first_name": "Test",
        "last_name": "User1",
        "email": "unique_test@example.com",
        "username": "uniqueuser",
        "password": "TestPass123",
    }

    User.register(db_session, user1)
    db_session.commit()

    user2 = {
        "first_name": "Test",
        "last_name": "User2",
        "email": "unique_test@example.com",  # duplicate
        "username": "differentuser",
        "password": "TestPass123",
    }

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, user2)


def test_short_password_registration(db_session):
    # password too short should fail
    data = {
        "first_name": "Password",
        "last_name": "Test",
        "email": "short.pass@example.com",
        "username": "shortpass",
        "password": "Shor1",
    }

    with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
        User.register(db_session, data)


def test_invalid_token():
    # invalid token should return None
    result = User.verify_token("invalid.token.string")
    assert result is None


def test_token_creation_and_verification(db_session, fake_user_data):
    # create + verify token
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()

    token = User.create_access_token({"sub": str(user.id)})
    decoded = User.verify_token(token)

    assert decoded == user.id


def test_authenticate_with_email(db_session, fake_user_data):
    # login using email instead of username
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(
        db_session,
        fake_user_data["email"],
        "TestPass123",
    )

    assert result is not None
    assert "access_token" in result


def test_user_model_representation(test_user):
    # __str__ check
    expected = f"<User(name={test_user.first_name} {test_user.last_name}, email={test_user.email})>"
    assert str(test_user) == expected


def test_missing_password_registration(db_session):
    # missing password should fail
    data = {
        "first_name": "NoPassword",
        "last_name": "Test",
        "email": "no.password@example.com",
        "username": "nopassworduser",
    }

    with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
        User.register(db_session, data)