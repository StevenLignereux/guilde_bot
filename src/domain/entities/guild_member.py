from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from src.infrastructure.config.database import Base

class GuildMember(Base):
    __tablename__ = "guild_members"

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, index=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(UTC))
    twitch_username = Column(String, nullable=True)
    social_role_id = Column(BigInteger, nullable=True) 