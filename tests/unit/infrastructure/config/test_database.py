import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
import sys

def test_init_db_success():
    # Arrange
    with patch('src.infrastructure.config.database.Base') as mock_base:
        with patch('src.infrastructure.config.database.engine') as mock_engine:
            mock_base.metadata.create_all = MagicMock()
            
            # Act
            from src.infrastructure.config.database import init_db
            init_db()
            
            # Assert
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)

def test_init_db_failure():
    # Arrange
    with patch('src.infrastructure.config.database.Base') as mock_base:
        mock_base.metadata.create_all = MagicMock(side_effect=Exception("Test error"))
        
        # Act & Assert
        with pytest.raises(Exception):
            from src.infrastructure.config.database import init_db
            init_db()

def test_get_db():
    # Test the database session generator
    from src.infrastructure.config.database import get_db
    db = next(get_db())
    assert db is not None
    try:
        next(get_db())
    except StopIteration:
        pass  # Expected behavior 

def test_database_url_postgres_conversion():
    with patch.dict('os.environ', {'Database_URL': 'postgres://user:pass@host/db'}):
        with patch('src.config.environment.load_environment', return_value={'database_url': 'postgres://user:pass@host/db'}):
            # Supprimer le module s'il est déjà importé
            if 'src.infrastructure.config.database' in sys.modules:
                del sys.modules['src.infrastructure.config.database']
            
            from src.infrastructure.config.database import DATABASE_URL
            assert DATABASE_URL.startswith('postgresql://')

def test_database_engine_creation_error():
    with patch('sqlalchemy.create_engine', side_effect=SQLAlchemyError("Test error")):
        with patch('src.config.environment.load_environment', return_value={'database_url': 'postgresql://test'}):
            # Supprimer le module s'il est déjà importé
            if 'src.infrastructure.config.database' in sys.modules:
                del sys.modules['src.infrastructure.config.database']
            
            with pytest.raises(SQLAlchemyError):
                from src.infrastructure.config.database import engine 