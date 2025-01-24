import pytest
from unittest.mock import Mock, patch
from src.infrastructure.repositories.guild_member_repository import GuildMemberRepository
from src.domain.entities.guild_member import GuildMember

@pytest.mark.asyncio
async def test_get_by_discord_id():
    # Arrange
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = GuildMember(
        discord_id=123456789,
        username="test_user",
        twitch_username="test_twitch"
    )
    
    with patch('src.infrastructure.repositories.postgres_repository.get_db', return_value=iter([mock_db])):
        repo = GuildMemberRepository()
        
        # Act
        result = await repo.get_by_discord_id(123456789)
        
        # Assert
        assert result is not None
        assert result.discord_id == 123456789
        assert result.username == "test_user"
        mock_db.query.assert_called_once_with(GuildMember)

@pytest.mark.asyncio
async def test_get_all_with_twitch():
    # Arrange
    mock_db = Mock()
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.all.return_value = [
        GuildMember(discord_id=123, username="user1", twitch_username="twitch1"),
        GuildMember(discord_id=456, username="user2", twitch_username="twitch2")
    ]
    
    with patch('src.infrastructure.repositories.postgres_repository.get_db', return_value=iter([mock_db])):
        repo = GuildMemberRepository()
        
        # Act
        results = await repo.get_all_with_twitch()
        
        # Assert
        assert len(results) == 2
        assert all(member.twitch_username is not None for member in results) 