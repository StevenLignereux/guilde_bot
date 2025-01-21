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
        self.check_streams.start()

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
        streams_url = f'https://api.twitch.tv/helix/streams?user_login={
            username}'
        streams_response = self.session.get(streams_url, headers=headers)
        streams_response.raise_for_status()
        streams_data = streams_response.json()['data']

        return streams_data

    async def send_streams_to_channel(self, channel, streams):
        for stream in streams:
            if stream['id'] not in self.stream_cache:
                embed = discord.Embed(
                    title=stream['title'],
                    url=f"https://www.twitch.tv/{stream['user_name']}",
                    description=stream['game_name'],
                    color=discord.Color.purple()
                )
                embed.set_author(name=stream['user_name'])
                embed.set_thumbnail(url=stream['thumbnail_url'])
                embed.add_field(
                    name="Viewers", value=stream['viewer_count'], inline=True)
                try:
                    await channel.send(embed=embed)
                    self.stream_cache.add(stream['id'])
                except discord.errors.Forbidden:
                    logging.error(
                        f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel.id}.")
                except discord.errors.HTTPException as e:
                    logging.error(
                        f"Erreur HTTP lors de l'envoi du message : {e}")
                except Exception as e:
                    logging.error(f"Erreur inattendue : {e}")

    @tasks.loop(seconds=5)
    async def check_streams(self):
        channel_id = int(os.getenv('SOCIAL_ID'))
        twitch_username = os.getenv('TWITCH_USERNAME')
        channel = self.bot.get_channel(channel_id)
        if channel:
            streams = await self.fetch_twitch_streams(twitch_username)
            await self.send_streams_to_channel(channel, streams)

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Streams(bot))
