from src.infrastructure.repositories.guild_member_repository import GuildMemberRepository
from src.domain.entities.guild_member import GuildMember

class MemberService:
    """
    Service de gestion des membres de la guilde.
    
    Gère les opérations liées aux membres : enregistrement, mise à jour
    des informations et association avec les comptes Twitch.
    
    Attributes:
        repository (GuildMemberRepository): Repository pour l'accès aux données des membres
    """

    def __init__(self):
        self.repository = GuildMemberRepository()
    
    async def register_member(self, discord_id: int, username: str):
        """
        Enregistre un nouveau membre dans la base de données.
        
        Args:
            discord_id (int): ID Discord du membre
            username (str): Nom d'utilisateur Discord
        """
        member = GuildMember(
            discord_id=discord_id,
            username=username
        )
        await self.repository.save(member)
    
    async def update_twitch_username(self, discord_id: int, twitch_username: str):
        """
        Met à jour le nom d'utilisateur Twitch d'un membre.
        
        Args:
            discord_id (int): ID Discord du membre
            twitch_username (str): Nouveau nom d'utilisateur Twitch
        """
        member = await self.repository.get_by_discord_id(discord_id)
        if member:
            member.twitch_username = twitch_username
            await self.repository.save(member) 