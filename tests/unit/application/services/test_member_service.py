import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.application.services.member_service import MemberService
from src.domain.entities.guild_member import GuildMember

@pytest.mark.asyncio
async def test_register_member():
    # Arrange
    with patch('src.infrastructure.repositories.guild_member_repository.GuildMemberRepository') as mock_repo:
        service = MemberService()
        mock_instance = AsyncMock()
        mock_instance.save = AsyncMock()
        service.repository = mock_instance
        
        # Act
        await service.register_member(123456789, "test_user")
        
        # Assert
        mock_instance.save.assert_called_once()

@pytest.mark.asyncio
async def test_update_twitch_username():
    # Arrange
    with patch('src.infrastructure.repositories.guild_member_repository.GuildMemberRepository') as mock_repo:
        service = MemberService()
        mock_instance = AsyncMock()
        mock_member = GuildMember(discord_id=123456789, username="test_user")
        mock_instance.get_by_discord_id = AsyncMock(return_value=mock_member)
        mock_instance.save = AsyncMock()
        service.repository = mock_instance
        
        # Act
        await service.update_twitch_username(123456789, "new_twitch")
        
        # Assert
        assert mock_member.twitch_username == "new_twitch"
        mock_instance.save.assert_called_once() 