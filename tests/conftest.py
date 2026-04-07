# tests/conftest.py

import subprocess
import time
import logging
from typing import Generator, Dict, List
from contextlib import contextmanager

import pytest
import requests
from faker import Faker
from playwright.sync_api import sync_playwright, Browser, Page
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database import Base, get_engine, get_sessionmaker
from app.models.user import User
from app.config import settings
from app.database_init import init_db, drop_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(12345)

logger.info(f"Using database URL: {settings.DATABASE_URL}")

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)


def create_fake_user() -> Dict[str, str]:
    """Returns a dict of randomly generated user data."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12)
    }


@contextmanager
def managed_db_session():
    """Context manager that opens a session and rolls back on any error."""
    session = TestingSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Polls the given URL until it responds 200 or the timeout is hit."""
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False


class ServerStartupError(Exception):
    """Raised when the test server fails to start."""
    pass


# ── Database fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(request):
    """
    Runs once per test session.
    Drops and recreates all tables so every session starts clean.
    """
    logger.info("Setting up test database...")
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    init_db()
    logger.info("Test database ready.")

    yield

    preserve_db = request.config.getoption("--preserve-db")
    if preserve_db:
        logger.info("Skipping drop_db due to --preserve-db flag.")
    else:
        logger.info("Cleaning up test database...")
        drop_db()


@pytest.fixture
def db_session(request) -> Generator[Session, None, None]:
    """
    Yields a database session for a single test.
    Truncates all tables afterward unless --preserve-db is passed.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        preserve_db = request.config.getoption("--preserve-db")
        if not preserve_db:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        session.close()


# ── Data fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    """Returns a single dict of fake user data."""
    return create_fake_user()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Creates, commits, and returns a single user in the test database."""
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    logger.info(f"Created test user with ID: {user.id}")
    return user


@pytest.fixture
def seed_users(db_session: Session, request) -> List[User]:
    """
    Seeds the database with multiple users (default 5).
    Override count with: @pytest.mark.parametrize('seed_users', [10], indirect=True)
    """
    try:
        num_users = request.param
    except AttributeError:
        num_users = 5

    users = []
    for _ in range(num_users):
        user_data = create_fake_user()
        user = User(**user_data)
        users.append(user)
        db_session.add(user)

    db_session.commit()
    logger.info(f"Seeded {len(users)} users.")
    return users


# ── Optional server fixture ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def fastapi_server():
    """Starts a local FastAPI server for integration tests that need HTTP."""
    server_url = 'http://127.0.0.1:8000/'
    logger.info("Starting test server...")

    try:
        process = subprocess.Popen(
            ['python', 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if not wait_for_server(server_url, timeout=30):
            raise ServerStartupError("Failed to start test server")

        logger.info("Test server started.")
        yield

    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        logger.info("Terminating test server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


# ── Optional browser fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context():
    """Launches a headless Chromium browser for UI tests."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture
def page(browser_context: Browser):
    """Opens a fresh browser page for each test."""
    context = browser_context.new_context(
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    try:
        yield page
    finally:
        page.close()
        context.close()


# ── CLI options ────────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption(
        "--preserve-db",
        action="store_true",
        default=False,
        help="Skip table truncation and dropping after tests."
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Include tests marked as slow."
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --run-slow is passed."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)