import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
import os, sys
print('RUNNING TEST FILE:', os.path.abspath(__file__))
print("PYTHONPATH:", sys.path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bot.db.database import User, Base, GoldDollarRial
print("User imported from:", User.__module__, "Dict:", dir(User))
print("User columns:", [c.name for c in User.__table__.columns])

@pytest.fixture(scope="function")
def session():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()
    clear_mappers()

def test_create_user(session):
    user = User(
        generated_id="abc123",
        name="John",
        first_name="John",
        last_name="Doe",
        gender="Male",
        age=30,
        city="Tehran",
        profile_photo="someurl",
        about="I am a test user.",
        latitude=35.6892,
        longitude=51.3890,
    )
    session.add(user)
    session.commit()
    retrieved = session.query(User).filter_by(generated_id="abc123").first()
    assert retrieved is not None
    assert retrieved.name == "John"
    assert retrieved.age == 30

def test_update_user(session):

    user = User(generated_id="abc123")
    session.add(user)
    session.commit()
    user_in_db = session.query(User).filter_by(generated_id="to_update").first()
    user_in_db.name = "UpdatedName"
    session.commit()
    updated = session.query(User).filter_by(generated_id="to_update").first()
    assert updated.name == "UpdatedName"

def test_delete_user(session):
    user = User(generated_id="to_delete")
    session.add(user)
    session.commit()
    session.delete(user)
    session.commit()
    assert session.query(User).filter_by(generated_id="to_delete").first() is None

def test_create_gold_dollar_rial(session):
    gold = GoldDollarRial(
        gold_18k_ir=123456.7,
        dollar_ir_rial=42000.0,
        time_check_ir="2025-07-07 00:00:00",
        gold_18k_international_dollar=50.0,
        gold_18k_international_rial=200000.0,
        time_check_int="2025-07-07 00:00:00"
    )
    session.add(gold)
    session.commit()
    result = session.query(GoldDollarRial).first()
    assert result.gold_18k_ir == 123456.7
    assert result.dollar_ir_rial == 42000.0

def test_user_repr_and_defaults(session):
    user = User(generated_id="default", name="A")
    session.add(user)
    session.commit()
    retrieved = session.query(User).filter_by(generated_id="default").first()
    assert retrieved.about == "No bio yet"