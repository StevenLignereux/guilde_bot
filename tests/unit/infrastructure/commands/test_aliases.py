"""
Tests pour le gestionnaire d'alias
"""
import pytest
from datetime import datetime, timedelta
from src.infrastructure.commands.aliases import AliasManager, CommandUsage

def test_add_alias():
    """Test l'ajout d'alias"""
    manager = AliasManager()
    
    # Test d'ajout d'un alias simple
    manager.add_alias("test", "t")
    assert manager.get_command_name("t") == "test"
    
    # Test d'ajout de plusieurs alias
    manager.add_alias("test", "test1")
    manager.add_alias("test", "test2")
    assert manager.get_command_name("test1") == "test"
    assert manager.get_command_name("test2") == "test"
    
    # Test d'ajout d'un alias déjà utilisé
    with pytest.raises(ValueError) as exc_info:
        manager.add_alias("autre", "t")
    assert "déjà utilisé" in str(exc_info.value)

def test_track_usage():
    """Test le suivi d'utilisation des commandes"""
    manager = AliasManager()
    
    # Ajouter une commande avec des alias
    manager.add_alias("test", "t")
    manager.add_alias("test", "test1")
    
    # Utiliser la commande avec différents noms
    manager.track_usage("test")  # Nom réel
    manager.track_usage("t")     # Alias 1
    manager.track_usage("test1") # Alias 2
    
    # Vérifier les statistiques
    usage = manager.get_usage("test")
    assert usage is not None
    assert usage.total_uses == 3
    assert usage.alias_uses["t"] == 1
    assert usage.alias_uses["test1"] == 1
    assert usage.last_used is not None

def test_get_usage():
    """Test la récupération des statistiques d'utilisation"""
    manager = AliasManager()
    
    # Test avec une commande inexistante
    assert manager.get_usage("inexistant") is None
    
    # Test avec une commande existante
    manager.add_alias("test", "t")
    manager.track_usage("test")
    
    usage = manager.get_usage("test")
    assert usage is not None
    assert usage.name == "test"
    assert usage.total_uses == 1
    assert len(usage.aliases) == 1
    assert usage.aliases[0] == "t"

def test_get_all_usages():
    """Test la récupération de toutes les statistiques"""
    manager = AliasManager()
    
    # Ajouter plusieurs commandes
    manager.add_alias("cmd1", "c1")
    manager.add_alias("cmd2", "c2")
    
    # Utiliser les commandes
    manager.track_usage("cmd1")
    manager.track_usage("c1")
    manager.track_usage("cmd2")
    
    # Vérifier les statistiques
    usages = manager.get_all_usages()
    assert len(usages) == 2
    
    cmd1_usage = next(u for u in usages if u.name == "cmd1")
    assert cmd1_usage.total_uses == 2
    
    cmd2_usage = next(u for u in usages if u.name == "cmd2")
    assert cmd2_usage.total_uses == 1

def test_get_aliases():
    """Test la récupération des alias d'une commande"""
    manager = AliasManager()
    
    # Test avec une commande inexistante
    assert manager.get_aliases("inexistant") == []
    
    # Test avec une commande existante
    manager.add_alias("test", "t")
    manager.add_alias("test", "test1")
    
    aliases = manager.get_aliases("test")
    assert len(aliases) == 2
    assert "t" in aliases
    assert "test1" in aliases 