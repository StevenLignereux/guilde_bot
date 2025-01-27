import pytest
from unittest.mock import AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from src.infrastructure.repositories.guild_member_repository import GuildMemberRepository
from src.domain.entities.guild_member import GuildMember

@pytest.mark.asyncio
async def test_get_by_discord_id():
    """Test la récupération d'un membre par son ID Discord"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_member = GuildMember(
        discord_id="123456789",
        username="test_user",
        twitch_username="test_twitch"
    )
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    result = await repo.get_by_discord_id("123456789")
    
    # Assert
    assert result.discord_id == "123456789"
    assert result.username == "test_user"
    assert result.twitch_username == "test_twitch"
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_discord_id_not_found():
    """Test la récupération d'un membre inexistant"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    result = await repo.get_by_discord_id("999999999")
    
    # Assert
    assert result is None
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_all_with_twitch():
    """Test la récupération de tous les membres avec un compte Twitch"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_members = [
        GuildMember(discord_id="123", username="user1", twitch_username="twitch1"),
        GuildMember(discord_id="456", username="user2", twitch_username="twitch2")
    ]
    mock_result.scalars.return_value.all.return_value = mock_members
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    result = await repo.get_all_with_twitch()
    
    # Assert
    assert len(result) == 2
    assert all(member.twitch_username for member in result)
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_all_with_twitch_empty():
    """Test la récupération des membres avec Twitch quand il n'y en a pas"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    result = await repo.get_all_with_twitch()
    
    # Assert
    assert len(result) == 0
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_link_twitch_account():
    """Test l'association d'un compte Twitch"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_member = GuildMember(
        discord_id="123456789",
        username="test_user"
    )
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    result = await repo.link_twitch_account("123456789", "test_twitch")
    
    # Assert
    assert result.discord_id == "123456789"
    assert result.twitch_username == "test_twitch"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_member)

@pytest.mark.asyncio
async def test_link_twitch_account_member_not_found():
    """Test l'association d'un compte Twitch à un membre inexistant"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    
    # Assert
    with pytest.raises(ValueError, match="Le membre avec l'ID Discord 999999999 n'existe pas"):
        await repo.link_twitch_account("999999999", "test_twitch")

@pytest.mark.asyncio
async def test_link_twitch_account_error():
    """Test la gestion des erreurs lors de l'association d'un compte Twitch"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_member = GuildMember(
        discord_id="123456789",
        username="test_user"
    )
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_db.execute.return_value = mock_result
    mock_db.commit.side_effect = SQLAlchemyError("Test error")
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    
    # Assert
    with pytest.raises(SQLAlchemyError):
        await repo.link_twitch_account("123456789", "test_twitch")
    mock_db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_unlink_twitch_account():
    """Test la dissociation d'un compte Twitch"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_member = GuildMember(
        discord_id="123456789",
        username="test_user",
        twitch_username="test_twitch"
    )
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    result = await repo.unlink_twitch_account("123456789")
    
    # Assert
    assert result.discord_id == "123456789"
    assert result.twitch_username is None
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_member)

@pytest.mark.asyncio
async def test_unlink_twitch_account_member_not_found():
    """Test la dissociation d'un compte Twitch d'un membre inexistant"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    
    # Assert
    with pytest.raises(ValueError, match="Le membre avec l'ID Discord 999999999 n'existe pas"):
        await repo.unlink_twitch_account("999999999")

@pytest.mark.asyncio
async def test_unlink_twitch_account_error():
    """Test la gestion des erreurs lors de la dissociation d'un compte Twitch"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_member = GuildMember(
        discord_id="123456789",
        username="test_user",
        twitch_username="test_twitch"
    )
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_db.execute.return_value = mock_result
    mock_db.commit.side_effect = SQLAlchemyError("Test error")
    
    # Act
    repo = GuildMemberRepository()
    repo.db = mock_db
    
    # Assert
    with pytest.raises(SQLAlchemyError):
        await repo.unlink_twitch_account("123456789")
    mock_db.rollback.assert_called_once() 