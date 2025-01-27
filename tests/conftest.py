import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.infrastructure.config.database import Base, get_session
from src.config.config import Config
from src.domain.entities.guild_member import GuildMember

# Override de la configuration de base de données pour les tests
@pytest.fixture(autouse=True)
def override_db_config(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///./test.db')

@pytest.fixture(scope="session")
def test_db():
    """Crée une base de données de test"""
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def db_session(test_db):
    """Fournit une session de base de données de test"""
    session = await get_session()
    try:
        yield session
    finally:
        await session.close()

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