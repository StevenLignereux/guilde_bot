import pytest
from src.infrastructure.commands.validators import (
    StringValidator, NumberValidator, ListValidator,
    validate_params, ValidationError
)

def test_string_validator_basic():
    """Test la validation basique des chaînes"""
    validator = StringValidator("test")
    assert validator.validate("hello") == "hello"
    
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(123)
    assert "chaîne de caractères" in str(exc_info.value)

def test_string_validator_length():
    """Test la validation de longueur des chaînes"""
    validator = StringValidator("test", min_length=2, max_length=5)
    
    # Test longueur minimale
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("a")
    assert "au moins 2 caractères" in str(exc_info.value)
    
    # Test longueur maximale
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("123456")
    assert "au maximum 5 caractères" in str(exc_info.value)
    
    # Test valeur valide
    assert validator.validate("hello") == "hello"

def test_string_validator_pattern():
    """Test la validation par expression régulière"""
    validator = StringValidator("test", pattern=r"^[A-Z][a-z]+$")
    
    assert validator.validate("Hello") == "Hello"
    
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("hello")
    assert "format attendu" in str(exc_info.value)

def test_number_validator_basic():
    """Test la validation basique des nombres"""
    validator = NumberValidator("test")
    
    assert validator.validate(42) == 42
    assert validator.validate(3.14) == 3.14
    
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("123")
    assert "nombre" in str(exc_info.value)

def test_number_validator_range():
    """Test la validation des plages de nombres"""
    validator = NumberValidator("test", min_value=0, max_value=100)
    
    # Test valeur minimale
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(-1)
    assert "supérieur ou égal à 0" in str(exc_info.value)
    
    # Test valeur maximale
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(101)
    assert "inférieur ou égal à 100" in str(exc_info.value)
    
    # Test valeur valide
    assert validator.validate(50) == 50

def test_number_validator_integer():
    """Test la validation des nombres entiers"""
    validator = NumberValidator("test", integer_only=True)
    
    assert validator.validate(42) == 42
    
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(3.14)
    assert "nombre entier" in str(exc_info.value)

def test_list_validator_basic():
    """Test la validation basique des listes"""
    item_validator = StringValidator("item")
    validator = ListValidator("test", item_validator)
    
    assert validator.validate(["a", "b", "c"]) == ["a", "b", "c"]
    
    with pytest.raises(ValidationError) as exc_info:
        validator.validate("not a list")
    assert "liste" in str(exc_info.value)

def test_list_validator_length():
    """Test la validation de longueur des listes"""
    item_validator = StringValidator("item")
    validator = ListValidator("test", item_validator, min_length=2, max_length=4)
    
    # Test longueur minimale
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(["a"])
    assert "au moins 2 éléments" in str(exc_info.value)
    
    # Test longueur maximale
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(["a", "b", "c", "d", "e"])
    assert "au maximum 4 éléments" in str(exc_info.value)
    
    # Test valeur valide
    assert validator.validate(["a", "b", "c"]) == ["a", "b", "c"]

def test_list_validator_items():
    """Test la validation des éléments de la liste"""
    item_validator = NumberValidator("item", min_value=0)
    validator = ListValidator("test", item_validator)
    
    # Test élément invalide
    with pytest.raises(ValidationError) as exc_info:
        validator.validate([1, -1, 2])
    assert "supérieur ou égal à 0" in str(exc_info.value)
    
    # Test valeur valide
    assert validator.validate([1, 2, 3]) == [1, 2, 3]

@pytest.mark.asyncio
async def test_validate_params_decorator():
    """Test le décorateur de validation des paramètres"""
    string_validator = StringValidator("name", min_length=3)
    number_validator = NumberValidator("age", min_value=0)
    
    @validate_params(name=string_validator, age=number_validator)
    async def test_command(self, ctx, name: str, age: int):
        return name, age
    
    # Test valeurs valides
    result = await test_command(None, None, name="John", age=25)
    assert result == ("John", 25)
    
    # Test valeur invalide
    with pytest.raises(ValidationError) as exc_info:
        await test_command(None, None, name="Jo", age=25)
    assert "au moins 3 caractères" in str(exc_info.value) 