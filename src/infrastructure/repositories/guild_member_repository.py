from typing import Optional, List
from sqlalchemy import select
from src.infrastructure.repositories.postgres_repository import PostgresRepository
from src.domain.entities.guild_member import GuildMember

class GuildMemberRepository(PostgresRepository[GuildMember]):
    def __init__(self):
        super().__init__(GuildMember)
    
    async def get_by_discord_id(self, discord_id: int) -> Optional[GuildMember]:
        return self.db.query(GuildMember).filter(GuildMember.discord_id == discord_id).first()
    
    async def get_all_with_twitch(self) -> List[GuildMember]:
        return self.db.query(GuildMember).filter(GuildMember.twitch_username.isnot(None)).all() 