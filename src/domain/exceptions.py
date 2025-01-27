class DomainError(Exception):
    """Classe de base pour toutes les exceptions du domaine"""
    pass

class RepositoryError(DomainError):
    """Classe de base pour les erreurs liées aux repositories"""
    pass

class TaskError(DomainError):
    """Classe de base pour les erreurs liées aux tâches"""
    pass

# Exceptions spécifiques pour le Repository
class TaskNotFoundError(RepositoryError):
    """Levée quand une tâche n'est pas trouvée"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Tâche non trouvée avec l'ID: {task_id}")

class DatabaseConnectionError(RepositoryError):
    """Levée lors d'un problème de connexion à la base de données"""
    def __init__(self, details: str):
        super().__init__(f"Erreur de connexion à la base de données: {details}")

# Exceptions spécifiques pour les Tâches
class InvalidTaskStateError(TaskError):
    """Levée quand une transition d'état de tâche est invalide"""
    def __init__(self, current_state: str, attempted_state: str):
        self.current_state = current_state
        self.attempted_state = attempted_state
        super().__init__(
            f"Transition invalide de l'état '{current_state}' vers '{attempted_state}'"
        )