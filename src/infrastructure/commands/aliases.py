"""
Gestion des alias pour les commandes slash
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CommandUsage:
    """Statistiques d'utilisation d'une commande"""
    name: str
    aliases: List[str] = field(default_factory=list)
    total_uses: int = 0
    last_used: Optional[datetime] = None
    alias_uses: Dict[str, int] = field(default_factory=dict)

class AliasManager:
    """Gestionnaire d'alias pour les commandes"""
    
    def __init__(self):
        self._aliases: Dict[str, str] = {}  # alias -> nom réel
        self._commands: Dict[str, CommandUsage] = {}  # nom réel -> statistiques
    
    def add_alias(self, command_name: str, alias: str) -> None:
        """Ajoute un alias pour une commande
        
        Args:
            command_name (str): Nom réel de la commande
            alias (str): Alias à ajouter
            
        Raises:
            ValueError: Si l'alias est déjà utilisé
        """
        if alias in self._aliases:
            raise ValueError(f"L'alias '{alias}' est déjà utilisé")
        
        self._aliases[alias] = command_name
        
        if command_name not in self._commands:
            self._commands[command_name] = CommandUsage(name=command_name)
        
        self._commands[command_name].aliases.append(alias)
        self._commands[command_name].alias_uses[alias] = 0
    
    def get_command_name(self, name: str) -> str:
        """Retourne le nom réel d'une commande à partir de son nom ou alias
        
        Args:
            name (str): Nom ou alias de la commande
            
        Returns:
            str: Nom réel de la commande
        """
        return self._aliases.get(name, name)
    
    def track_usage(self, name: str) -> None:
        """Enregistre l'utilisation d'une commande
        
        Args:
            name (str): Nom ou alias utilisé
        """
        real_name = self.get_command_name(name)
        
        if real_name not in self._commands:
            self._commands[real_name] = CommandUsage(name=real_name)
        
        command = self._commands[real_name]
        command.total_uses += 1
        command.last_used = datetime.now()
        
        if name in command.alias_uses:
            command.alias_uses[name] += 1
    
    def get_usage(self, command_name: str) -> Optional[CommandUsage]:
        """Retourne les statistiques d'utilisation d'une commande
        
        Args:
            command_name (str): Nom réel de la commande
            
        Returns:
            Optional[CommandUsage]: Statistiques d'utilisation ou None si la commande n'existe pas
        """
        real_name = self.get_command_name(command_name)
        return self._commands.get(real_name)
    
    def get_all_usages(self) -> List[CommandUsage]:
        """Retourne les statistiques d'utilisation de toutes les commandes
        
        Returns:
            List[CommandUsage]: Liste des statistiques d'utilisation
        """
        return list(self._commands.values())
    
    def get_aliases(self, command_name: str) -> List[str]:
        """Retourne la liste des alias d'une commande
        
        Args:
            command_name (str): Nom réel de la commande
            
        Returns:
            List[str]: Liste des alias
        """
        real_name = self.get_command_name(command_name)
        if real_name in self._commands:
            return self._commands[real_name].aliases
        return [] 