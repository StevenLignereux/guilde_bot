import pytest
from unittest.mock import patch
import os
from src.config.environment import load_environment

def test_load_environment_file_not_found():
    """Le fichier .env n'est pas trouvé, mais ce n'est pas une erreur car on utilise les variables système"""
    with patch('os.path.exists', return_value=False), \
         patch('os.getenv') as mock_getenv:
        # Simuler des variables d'environnement valides
        mock_getenv.side_effect = lambda key: {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db',
            'DISCORD_TOKEN': 'token123'
        }.get(key)
        
        # Ne devrait pas lever d'erreur
        config = load_environment()
        assert config['database_url'] == 'postgresql://user:pass@localhost/db'
        assert config['DISCORD_TOKEN'] == 'token123'

def test_load_environment_missing_database_url():
    """Test que l'absence de DATABASE_URL lève une ValueError"""
    with patch('os.path.exists', return_value=True), \
         patch('dotenv.load_dotenv', return_value=True), \
         patch('os.getenv', return_value=None):
        with pytest.raises(ValueError, match="La variable DATABASE_URL ou Database_URL est requise"):
            load_environment()

def test_load_environment_missing_discord_token():
    """Test que l'absence de DISCORD_TOKEN lève une ValueError"""
    with patch('os.path.exists', return_value=True), \
         patch('dotenv.load_dotenv', return_value=True), \
         patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda key: {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db',
            'DISCORD_TOKEN': None
        }.get(key)
        
        with pytest.raises(ValueError, match="La variable DISCORD_TOKEN est requise"):
            load_environment() 