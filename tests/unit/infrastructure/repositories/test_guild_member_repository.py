import pytest
from unittest.mock import AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from src.infrastructure.repositories.guild_member_repository import GuildMemberRepository
from src.domain.entities.guild_member import GuildMember
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_get_by_discord_id():
    """Test la récupération d'un membre par son ID Discord"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"
    member = GuildMember(discord_id=discord_id)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = member
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act
    result = await repo.get_by_discord_id(discord_id)

    # Assert
    assert result is not None
    assert str(result.discord_id) == discord_id

@pytest.mark.asyncio
async def test_get_by_discord_id_not_found():
    """Test la récupération d'un membre inexistant"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act
    result = await repo.get_by_discord_id(discord_id)

    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_get_all_with_twitch():
    """Test la récupération de tous les membres avec un compte Twitch"""
    # Arrange
    repo = GuildMemberRepository()
    members = [
        GuildMember(discord_id="1", twitch_username="user1"),
        GuildMember(discord_id="2", twitch_username="user2")
    ]

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = members
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act
    result = await repo.get_all_with_twitch()

    # Assert
    assert result == members

@pytest.mark.asyncio
async def test_get_all_with_twitch_empty():
    """Test la récupération des membres avec Twitch quand il n'y en a pas"""
    # Arrange
    repo = GuildMemberRepository()

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act
    result = await repo.get_all_with_twitch()

    # Assert
    assert result == []

@pytest.mark.asyncio
async def test_link_twitch_account():
    """Test l'association d'un compte Twitch"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"
    twitch_username = "test_user"
    member = GuildMember(discord_id=discord_id)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = member
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act
    result = await repo.link_twitch_account(discord_id, twitch_username)

    # Assert
    assert result is not None
    assert str(result.discord_id) == discord_id
    assert str(result.twitch_username) == twitch_username

@pytest.mark.asyncio
async def test_link_twitch_account_member_not_found():
    """Test l'association d'un compte Twitch à un membre inexistant"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"
    twitch_username = "test_user"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match="Membre non trouvé"):
        await repo.link_twitch_account(discord_id, twitch_username)

@pytest.mark.asyncio
async def test_link_twitch_account_error():
    """Test la gestion des erreurs lors de l'association d'un compte Twitch"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"
    twitch_username = "test_user"
    member = GuildMember(discord_id=discord_id)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = member
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(
        __aenter__=AsyncMock(),
        __aexit__=AsyncMock(side_effect=SQLAlchemyError("Test error"))
    ))
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.link_twitch_account(discord_id, twitch_username)

@pytest.mark.asyncio
async def test_unlink_twitch_account():
    """Test la dissociation d'un compte Twitch"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"
    member = GuildMember(discord_id=discord_id, twitch_username="test_user")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = member
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act
    result = await repo.unlink_twitch_account(discord_id)

    # Assert
    assert result is not None
    assert str(result.discord_id) == discord_id
    assert result.twitch_username is None

@pytest.mark.asyncio
async def test_unlink_twitch_account_member_not_found():
    """Test la dissociation d'un compte Twitch d'un membre inexistant"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock()))
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match="Membre non trouvé"):
        await repo.unlink_twitch_account(discord_id)

@pytest.mark.asyncio
async def test_unlink_twitch_account_error():
    """Test la gestion des erreurs lors de la dissociation d'un compte Twitch"""
    # Arrange
    repo = GuildMemberRepository()
    discord_id = "123456789"
    member = GuildMember(discord_id=discord_id, twitch_username="test_user")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = member
    mock_session.execute.return_value = mock_result
    mock_session.begin = AsyncMock(return_value=AsyncMock(
        __aenter__=AsyncMock(),
        __aexit__=AsyncMock(side_effect=SQLAlchemyError("Test error"))
    ))
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.unlink_twitch_account(discord_id) 