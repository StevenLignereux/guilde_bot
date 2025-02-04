from typing import Protocol

class Service(Protocol):
    """
    Protocole de base pour tous les services de l'application.
    
    Définit l'interface commune que tous les services doivent implémenter.
    Utilise le typing.Protocol pour le typage statique et la vérification
    de conformité des implémentations.
    """