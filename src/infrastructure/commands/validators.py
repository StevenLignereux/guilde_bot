"""
Validateurs pour les paramètres des commandes
"""
from typing import Any, Optional, Union, List
from discord.ext import commands
import re
from ..errors.exceptions import ValidationError

class Validator:
    """Classe de base pour les validateurs"""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def validate(self, value: Any) -> Any:
        """Valide une valeur"""
        raise NotImplementedError

class StringValidator(Validator):
    """Validateur pour les chaînes de caractères"""
    
    def __init__(self, field_name: str, min_length: Optional[int] = None,
                 max_length: Optional[int] = None, pattern: Optional[str] = None):
        super().__init__(field_name)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern and re.compile(pattern)
    
    def validate(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(self.field_name, value, "doit être une chaîne de caractères")
        
        if self.min_length and len(value) < self.min_length:
            raise ValidationError(
                self.field_name,
                value,
                f"doit contenir au moins {self.min_length} caractères"
            )
        
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(
                self.field_name,
                value,
                f"doit contenir au maximum {self.max_length} caractères"
            )
        
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(
                self.field_name,
                value,
                "ne correspond pas au format attendu"
            )
        
        return value

class NumberValidator(Validator):
    """Validateur pour les nombres"""
    
    def __init__(self, field_name: str, min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None, integer_only: bool = False):
        super().__init__(field_name)
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
    
    def validate(self, value: Union[int, float]) -> Union[int, float]:
        if self.integer_only and not isinstance(value, int):
            raise ValidationError(self.field_name, value, "doit être un nombre entier")
        
        if not isinstance(value, (int, float)):
            raise ValidationError(self.field_name, value, "doit être un nombre")
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                self.field_name,
                value,
                f"doit être supérieur ou égal à {self.min_value}"
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                self.field_name,
                value,
                f"doit être inférieur ou égal à {self.max_value}"
            )
        
        return value

class ListValidator(Validator):
    """Validateur pour les listes"""
    
    def __init__(self, field_name: str, item_validator: Validator,
                 min_length: Optional[int] = None, max_length: Optional[int] = None):
        super().__init__(field_name)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: List[Any]) -> List[Any]:
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.field_name, value, "doit être une liste")
        
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                self.field_name,
                value,
                f"doit contenir au moins {self.min_length} éléments"
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                self.field_name,
                value,
                f"doit contenir au maximum {self.max_length} éléments"
            )
        
        return [self.item_validator.validate(item) for item in value]

def validate_params(**validators: Validator):
    """Décorateur pour valider les paramètres d'une commande"""
    def decorator(func):
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):
            # Valider chaque paramètre
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    kwargs[param_name] = validator.validate(kwargs[param_name])
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator 