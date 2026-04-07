# tests/auth/test_database.py

import pytest
import sys
import importlib
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

DATABASE_MODULE = "app.database"


@pytest.fixture
def mock_settings(monkeypatch):
    # mock DATABASE_URL before importing module
    mock = MagicMock()
    mock.DATABASE_URL = "postgresql://user:password@localhost:5432/test_db"

    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]

    monkeypatch.setattr(f"{DATABASE_MODULE}.settings", mock)
    return mock


def reload_database_module():
    # reload module after applying patches
    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    return importlib.import_module(DATABASE_MODULE)


def test_base_declaration(mock_settings):
    # Base should be declarative base
    database = reload_database_module()

    Base = database.Base
    assert isinstance(Base, database.declarative_base().__class__)


def test_get_engine_success(mock_settings):
    # engine should be created successfully
    database = reload_database_module()

    engine = database.get_engine()
    assert isinstance(engine, Engine)


def test_get_engine_failure(mock_settings):
    # engine creation failure should raise error
    database = reload_database_module()

    with patch("app.database.create_engine", side_effect=SQLAlchemyError("Engine error")):
        with pytest.raises(SQLAlchemyError, match="Engine error"):
            database.get_engine()


def test_get_sessionmaker(mock_settings):
    # sessionmaker should be created correctly
    database = reload_database_module()

    engine = database.get_engine()
    SessionLocal = database.get_sessionmaker(engine)

    assert isinstance(SessionLocal, sessionmaker)