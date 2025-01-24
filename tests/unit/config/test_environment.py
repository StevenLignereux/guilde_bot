import pytest
from unittest.mock import patch
import os
from src.config.environment import load_environment

def test_load_environment_file_not_found():
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(OSError, match="Fichier .env non trouvé"):
            load_environment()

def test_load_environment_missing_database_url():
    with patch('pathlib.Path.exists', return_value=True):
        with patch('dotenv.load_dotenv', return_value=True):
            with patch.object(os.environ, 'get', return_value=None):
                with pytest.raises(OSError, match="La variable Database_URL n'est pas définie"):
                    load_environment() 