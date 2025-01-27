import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
import sys
from src.config.config import DatabaseConfig
from src.infrastructure.config.database import init_db, get_db, get_test_session, DATABASE_URL

@pytest.mark.asyncio
async def test_init_db_success():
    """Test l'initialisation réussie de la base de données"""
    # Arrange
    config = DatabaseConfig(
        url="postgresql+asyncpg://user:pass@localhost/db",
        pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )
    mock_engine = AsyncMock()
    mock_conn = AsyncMock()
    mock_engine.connect.return_value = mock_conn
    mock_conn.__aenter__.return_value = mock_conn
    
    with patch('src.infrastructure.config.database.create_async_engine', return_value=mock_engine):
        # Act
        await init_db(config)
        
        # Assert
        mock_engine.connect.assert_called_once()
        mock_conn.close.assert_called_once()

@pytest.mark.asyncio
async def test_database_engine_creation_error():
    """Test la gestion des erreurs lors de la création du moteur de base de données"""
    # Arrange
    mock_create_engine = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    
    with patch('src.infrastructure.config.database.create_async_engine', mock_create_engine):
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await init_db()

@pytest.mark.asyncio
async def test_get_db_success():
    """Test la récupération réussie d'une session de base de données"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = AsyncMock(return_value=mock_session)
    
    with patch('src.infrastructure.config.database.async_session', mock_session_factory):
        # Act
        async with get_db() as session:
            # Assert
            assert isinstance(session, AsyncSession)
            mock_session_factory.assert_called_once()

@pytest.mark.asyncio
async def test_get_db_with_error():
    """Test la gestion des erreurs lors de l'utilisation d'une session"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = AsyncMock(return_value=mock_session)
    test_error = SQLAlchemyError("Test error")
    
    with patch('src.infrastructure.config.database.async_session', mock_session_factory):
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            async with get_db() as session:
                raise test_error
        
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

def test_get_test_session():
    """Test la récupération d'une session de test"""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session_factory = AsyncMock(return_value=mock_session)
    
    with patch('src.infrastructure.config.database.async_session', mock_session_factory):
        # Act
        session = get_test_session()
        
        # Assert
        assert isinstance(session, AsyncSession)
        mock_session_factory.assert_called_once()

@pytest.mark.asyncio
async def test_database_url_postgres_conversion():
    """Test la conversion de l'URL de la base de données de postgres:// à postgresql://"""
    # Arrange
    config = DatabaseConfig(url="postgres://user:pass@localhost/db")
    mock_engine = AsyncMock()
    mock_conn = AsyncMock()
    mock_engine.connect.return_value = mock_conn
    mock_conn.__aenter__.return_value = mock_conn
    
    with patch('src.infrastructure.config.database.create_async_engine') as mock_create_engine:
        # Act
        await init_db(config)
        
        # Assert
        mock_create_engine.assert_called_once()
        call_args = mock_create_engine.call_args[0][0]
        assert call_args.startswith('postgresql+asyncpg://')

def test_database_engine_creation_error():
    with patch('sqlalchemy.create_engine', side_effect=SQLAlchemyError("Test error")):
        with patch('src.config.environment.load_environment', return_value={'database_url': 'postgresql://test'}):
            # Supprimer le module s'il est déjà importé
            if 'src.infrastructure.config.database' in sys.modules:
                del sys.modules['src.infrastructure.config.database']
            
            with pytest.raises(SQLAlchemyError):
                from src.infrastructure.config.database import engine 