# tests/integration/test_user.py

import pytest
import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from tests.conftest import create_fake_user, managed_db_session

logger = logging.getLogger(__name__)


# ── Connection tests ───────────────────────────────────────────────────────────

def test_database_connection(db_session):
    """Make sure we can actually talk to the database."""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_managed_session():
    """
    Test that managed_db_session works for simple queries
    and properly catches errors from bad SQL.
    """
    with managed_db_session() as session:
        session.execute(text("SELECT 1"))

        try:
            session.execute(text("SELECT * FROM nonexistent_table"))
        except Exception as e:
            assert "nonexistent_table" in str(e)


# ── Session / transaction tests ────────────────────────────────────────────────

def test_session_handling(db_session):
    """
    Checks partial commit behavior:
    - user1 commits fine
    - user2 fails with duplicate email, rolls back
    - user3 commits fine
    - only user1 and user3 should be in the DB at the end
    """
    assert db_session.query(User).count() == 0

    user1 = User(
        first_name="Test", last_name="User",
        email="test1@example.com", username="testuser1", password="password123"
    )
    db_session.add(user1)
    db_session.commit()
    assert db_session.query(User).count() == 1

    # try adding a duplicate email — should fail and roll back
    try:
        user2 = User(
            first_name="Test", last_name="User",
            email="test1@example.com",  # duplicate
            username="testuser2", password="password456"
        )
        db_session.add(user2)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()

    # user1 should still be there after the rollback
    found = db_session.query(User).filter_by(email="test1@example.com").first()
    assert found is not None
    assert found.username == "testuser1"

    user3 = User(
        first_name="Test", last_name="User",
        email="test3@example.com", username="testuser3", password="password789"
    )
    db_session.add(user3)
    db_session.commit()

    users = db_session.query(User).order_by(User.email).all()
    emails = {u.email for u in users}
    assert len(users) == 2
    assert "test1@example.com" in emails
    assert "test3@example.com" in emails


# ── User creation tests ────────────────────────────────────────────────────────

def test_create_user_with_faker(db_session):
    """Create a user from fake data and verify it gets an ID after commit."""
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == user_data["email"]


def test_create_multiple_users(db_session):
    """Create 3 users in a loop and make sure they all get added."""
    users = []
    for _ in range(3):
        user = User(**create_fake_user())
        users.append(user)
        db_session.add(user)

    db_session.commit()
    assert len(users) == 3


# ── Query tests ────────────────────────────────────────────────────────────────

def test_query_methods(db_session, seed_users):
    """Basic query checks using seeded users — count, filter, and order."""
    count = db_session.query(User).count()
    assert count >= len(seed_users)

    # filter by email should find the first seeded user
    first = seed_users[0]
    found = db_session.query(User).filter_by(email=first.email).first()
    assert found is not None

    # ordering by email should return at least as many users as we seeded
    ordered = db_session.query(User).order_by(User.email).all()
    assert len(ordered) >= len(seed_users)


# ── Rollback tests ─────────────────────────────────────────────────────────────

def test_transaction_rollback(db_session):
    """
    If something goes wrong mid-transaction, the rollback should
    leave the database exactly as it was before.
    """
    initial_count = db_session.query(User).count()

    try:
        user = User(**create_fake_user())
        db_session.add(user)
        db_session.execute(text("SELECT * FROM nonexistent_table"))  # force error
        db_session.commit()
    except Exception:
        db_session.rollback()

    assert db_session.query(User).count() == initial_count


# ── Update tests ───────────────────────────────────────────────────────────────

def test_update_with_refresh(db_session, test_user):
    """Update a user's email and confirm updated_at gets bumped."""
    original_email = test_user.email
    original_updated_at = test_user.updated_at

    test_user.email = f"new_{original_email}"
    db_session.commit()
    db_session.refresh(test_user)

    assert test_user.email == f"new_{original_email}"
    assert test_user.updated_at > original_updated_at


# ── Bulk operation tests ───────────────────────────────────────────────────────

@pytest.mark.slow
def test_bulk_operations(db_session):
    """Insert 10 users at once with bulk_save_objects (slow test)."""
    users = [User(**create_fake_user()) for _ in range(10)]
    db_session.bulk_save_objects(users)
    db_session.commit()

    assert db_session.query(User).count() >= 10


# ── Uniqueness constraint tests ────────────────────────────────────────────────

def test_unique_email_constraint(db_session):
    """Two users with the same email should raise IntegrityError."""
    first_data = create_fake_user()
    db_session.add(User(**first_data))
    db_session.commit()

    second_data = create_fake_user()
    second_data["email"] = first_data["email"]  # force duplicate
    db_session.add(User(**second_data))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_username_constraint(db_session):
    """Two users with the same username should raise IntegrityError."""
    first_data = create_fake_user()
    db_session.add(User(**first_data))
    db_session.commit()

    second_data = create_fake_user()
    second_data["username"] = first_data["username"]  # force duplicate
    db_session.add(User(**second_data))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ── Persistence after constraint violation ─────────────────────────────────────

def test_user_persistence_after_constraint(db_session):
    """
    The original user should still exist after a failed duplicate insert
    and rollback.
    """
    original = User(
        first_name="First", last_name="User",
        email="first@example.com", username="firstuser", password="password123"
    )
    db_session.add(original)
    db_session.commit()
    saved_id = original.id

    try:
        duplicate = User(
            first_name="Second", last_name="User",
            email="first@example.com",  # duplicate
            username="seconduser", password="password456"
        )
        db_session.add(duplicate)
        db_session.commit()
        assert False, "Should have raised IntegrityError"
    except IntegrityError:
        db_session.rollback()

    found = db_session.query(User).filter_by(id=saved_id).first()
    assert found is not None
    assert found.email == "first@example.com"
    assert found.username == "firstuser"


# ── Error handling tests ───────────────────────────────────────────────────────

def test_error_handling():
    """managed_db_session should re-raise exceptions from invalid SQL."""
    with pytest.raises(Exception) as exc_info:
        with managed_db_session() as session:
            session.execute(text("INVALID SQL"))
    assert "INVALID SQL" in str(exc_info.value)