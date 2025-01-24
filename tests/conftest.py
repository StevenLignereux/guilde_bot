import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.config.database import Base, get_db
from src.domain.entities.guild_member import GuildMember

# Override de la configuration de base de données pour les tests
@pytest.fixture(autouse=True)
def override_db_config(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///./test.db')

@pytest.fixture(scope="function")
def test_engine():
    database_url = "sqlite:///:memory:"  # Utiliser une base de données en mémoire
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close() 