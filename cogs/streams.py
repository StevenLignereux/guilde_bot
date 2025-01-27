import discord
from discord.ext import commands, tasks
import requests
import os
import logging


class Streams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = requests.Session()
        self.stream_cache = set()

    @commands.Cog.listener()
    async def on_ready(self):
        """Démarrer la tâche de vérification des streams une fois que le bot est prêt"""
        self.check_streams.start()

    def cog_unload(self):
        """Arrêter la tâche quand le cog est déchargé"""
        self.check_streams.cancel()

    async def fetch_twitch_streams(self, username):
        client_id = os.getenv('TWITCH_CLIENT_ID')
        client_secret = os.getenv('TWITCH_CLIENT_SECRET')
        token_url = 'https://id.twitch.tv/oauth2/token'
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        token_response = self.session.post(token_url, data=token_data)
        token_response.raise_for_status()
        access_token = token_response.json()['access_token']

        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }
        streams_url = f'https://api.twitch.tv/helix/streams?user_login={username}'
        streams_response = self.session.get(streams_url, headers=headers)
        streams_response.raise_for_status()
        streams_data = streams_response.json()['data']

        return streams_data

    @tasks.loop(seconds=60)
    async def check_streams(self):
        """Vérifie les streams toutes les minutes"""
        try:
            channel_id = int(os.getenv('STREAM_CHANNEL_ID'))
            twitch_username = os.getenv('TWITCH_USERNAME')
            
            if not channel_id or not twitch_username:
                logging.error("Configuration des streams manquante")
                return
                
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logging.error(f"Canal des streams non trouvé (ID: {channel_id})")
                return
                
            streams = await self.fetch_twitch_streams(twitch_username)
            await self.send_streams_to_channel(channel, streams)
        except Exception as e:
            logging.error(f"Erreur lors de la vérification des streams : {str(e)}")

    async def send_streams_to_channel(self, channel, streams):
        """Envoie les notifications de stream dans le canal approprié"""
        if not streams:
            return

        for stream in streams:
            stream_id = stream['id']
            if stream_id not in self.stream_cache:
                embed = discord.Embed(
                    title=f"🎮 {stream['user_name']} est en live !",
                    description=stream['title'],
                    url=f"https://twitch.tv/{stream['user_login']}",
                    color=discord.Color.purple()
                )
                
                if stream.get('thumbnail_url'):
                    thumbnail_url = stream['thumbnail_url'].replace('{width}', '1280').replace('{height}', '720')
                    embed.set_image(url=thumbnail_url)
                
                embed.add_field(name="Jeu", value=stream['game_name'], inline=True)
                embed.add_field(name="Viewers", value=str(stream['viewer_count']), inline=True)
                
                await channel.send(embed=embed)
                self.stream_cache.add(stream_id)

async def setup(bot):
    await bot.add_cog(Streams(bot))
