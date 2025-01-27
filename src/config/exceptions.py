class ConfigError(Exception):
    """Erreur de base pour les erreurs de configuration"""
    pass

class EnvironmentVariableError(ConfigError):
    """Erreur levée quand une variable d'environnement requise est manquante"""
    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        super().__init__(f"La variable d'environnement {variable_name} est requise")

class InvalidEnvironmentError(ConfigError):
    """Erreur levée quand l'environnement spécifié est invalide"""
    def __init__(self, env: str, valid_envs: list):
        self.env = env
        self.valid_envs = valid_envs
        super().__init__(
            f"Environnement invalide : {env}. "
            f"Les environnements valides sont : {', '.join(valid_envs)}"
        )

class ResourceNotFoundError(ConfigError):
    """Erreur levée quand une ressource requise n'est pas trouvée"""
    def __init__(self, resource_path: str):
        self.resource_path = resource_path
        super().__init__(f"La ressource {resource_path} n'a pas été trouvée") 