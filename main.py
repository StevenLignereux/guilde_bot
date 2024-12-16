import discord
import requests
from bs4 import BeautifulSoup
import asyncio
from dotenv import load_dotenv
import os
import logging
from keep_alive import keep_alive

# Configurer le logging
logging.basicConfig(level=logging.INFO)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les variables d'environnement
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SOCIAL_ID = int(os.getenv('SOCIAL_ID'))
OTHER_BOT_COMMAND = os.getenv('OTHER_BOT_COMMAND')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_USERNAME = os.getenv('TWITCH_USERNAME')

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Utiliser une session HTTP pour réutiliser les connexions
session = requests.Session()

# Cache pour les news et les streams
news_cache = set()
stream_cache = set()

# NEWS
async def fetch_swtor_news():
    url = 'https://www.swtor.com/fr/info/news'
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    news_items = []
    base_url = 'https://www.swtor.com/'
    for article in soup.find_all('div', class_='newsItem'):
        title = article.find('h2').text.strip()
        description = article.find('span', class_='newsDesc').text.strip()
        link = article.find('a')['href']
        full_link = base_url + link
        image_tag = article.find('img')
        image_url = base_url + image_tag['src'] if image_tag else None
        news_items.append({'title': title, 'description': description, 'link': full_link, 'image_url': image_url})

    return news_items

async def send_news_to_channel(channel_id, news_items):
    channel = client.get_channel(channel_id)
    if channel:
        for item in news_items:
            if item['link'] not in news_cache:
                embed = discord.Embed(
                    title=item['title'],
                    url=item['link'],
                    description=item['description'],
                    color=discord.Color.blue()
                )
                embed.set_author(name="SWTOR News")
                embed.set_footer(text="SWTOR News", icon_url="https://www.swtor.com/favicon.ico")
                if item['image_url']:
                    embed.set_image(url=item['image_url'])
                embed.add_field(name="Lien", value=f"[Lire plus]({item['link']})", inline=False)
                try:
                    await channel.send(embed=embed)
                    news_cache.add(item['link'])
                except discord.errors.Forbidden:
                    logging.error(f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
                except discord.errors.HTTPException as e:
                    logging.error(f"Erreur HTTP lors de l'envoi du message : {e}")
                except Exception as e:
                    logging.error(f"Erreur inattendue : {e}")

# STREAM
async def get_twitch_access_token():
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = session.post(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data['access_token']

async def check_twitch_stream(username, access_token):
    url = f'https://api.twitch.tv/helix/streams?user_login={username}'
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    response = session.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data['data']

async def send_stream_announcement(channel_id, stream_info):
    channel = client.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title=f"{stream_info['user_name']} est en ligne !",
            url=f"https://www.twitch.tv/{stream_info['user_name']}",
            description=stream_info['title'],
            color=discord.Color.purple()
        )
        embed.set_author(name=stream_info['user_name'], icon_url=stream_info['profile_image_url'])
        embed.set_thumbnail(url=stream_info['thumbnail_url'].format(width=320, height=180))
        embed.add_field(name="Jeu", value=stream_info['game_name'], inline=False)
        embed.add_field(name="Vues", value=stream_info['viewer_count'], inline=False)
        embed.set_footer(text="Regardez le stream maintenant !")
        try:
            await channel.send(embed=embed)
            stream_cache.add(stream_info['id'])
        except discord.errors.Forbidden:
            logging.error(f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
        except discord.errors.HTTPException as e:
            logging.error(f"Erreur HTTP lors de l'envoi du message : {e}")
        except Exception as e:
            logging.error(f"Erreur inattendue : {e}")

async def check_news():
    await client.wait_until_ready()
    while True:
        news_items = await fetch_swtor_news()
        await send_news_to_channel(CHANNEL_ID, news_items)
        await asyncio.sleep(3600)  # Attendre 1 heure avant de récupérer les news à nouveau

async def check_streams():
    await client.wait_until_ready()
    access_token = await get_twitch_access_token()
    while True:
        stream_info = await check_twitch_stream(TWITCH_USERNAME, access_token)
        if stream_info and stream_info[0]['id'] not in stream_cache:
            await send_stream_announcement(SOCIAL_ID, stream_info[0])
        await asyncio.sleep(60)  # Vérifier toutes les minutes

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    client.loop.create_task(check_news())
    client.loop.create_task(check_streams())

keep_alive()
client.run(TOKEN)
