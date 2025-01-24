from src.infrastructure.repositories.guild_member_repository import GuildMemberRepository
from src.domain.entities.guild_member import GuildMember

class MemberService:
    def __init__(self):
        self.repository = GuildMemberRepository()
    
    async def register_member(self, discord_id: int, username: str):
        member = GuildMember(
            discord_id=discord_id,
            username=username
        )
        await self.repository.save(member)
    
    async def update_twitch_username(self, discord_id: int, twitch_username: str):
        member = await self.repository.get_by_discord_id(discord_id)
        if member:
            member.twitch_username = twitch_username
            await self.repository.save(member) 