from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.infrastructure.repositories.postgres_repository import PostgresRepository
from src.domain.entities.guild_member import GuildMember

class GuildMemberRepository(PostgresRepository[GuildMember]):
    """Repository pour les membres de la guilde"""
    
    def __init__(self):
        super().__init__(GuildMember)
    
    async def get_by_discord_id(self, discord_id: str) -> Optional[GuildMember]:
        """Récupère un membre par son ID Discord"""
        query = select(GuildMember).filter_by(discord_id=discord_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_with_twitch(self) -> List[GuildMember]:
        """Récupère tous les membres qui ont un compte Twitch associé"""
        query = select(GuildMember).filter(GuildMember.twitch_username.isnot(None))
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def link_twitch_account(self, discord_id: str, twitch_username: str) -> GuildMember:
        """Associe un compte Twitch à un membre"""
        try:
            # Récupérer le membre
            member = await self.get_by_discord_id(discord_id)
            if not member:
                raise ValueError(f"Le membre avec l'ID Discord {discord_id} n'existe pas")
            
            # Mettre à jour le compte Twitch
            member.twitch_username = twitch_username
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise
    
    async def unlink_twitch_account(self, discord_id: str) -> GuildMember:
        """Dissocie le compte Twitch d'un membre"""
        try:
            # Récupérer le membre
            member = await self.get_by_discord_id(discord_id)
            if not member:
                raise ValueError(f"Le membre avec l'ID Discord {discord_id} n'existe pas")
            
            # Supprimer le compte Twitch
            member.twitch_username = None
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise 