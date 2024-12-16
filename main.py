import discord
import requests
from bs4 import BeautifulSoup
import asyncio
from dotenv import load_dotenv
import os
import logging
from keep_alive import keep_alive
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

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
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
# Chemin vers l'image de fond locale
WELCOME_IMAGE_PATH = os.getenv('WELCOME_IMAGE_PATH')


intents = discord.Intents.default()
intents.members = True
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
        news_items.append({'title': title, 'description': description,
                          'link': full_link, 'image_url': image_url})

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
                embed.set_footer(text="SWTOR News",
                                 icon_url="https://www.swtor.com/favicon.ico")
                if item['image_url']:
                    embed.set_image(url=item['image_url'])
                embed.add_field(
                    name="Lien", value=f"[Lire plus]({item['link']})", inline=False)
                try:
                    await channel.send(embed=embed)
                    news_cache.add(item['link'])
                except discord.errors.Forbidden:
                    logging.error(
                        f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
                except discord.errors.HTTPException as e:
                    logging.error(
                        f"Erreur HTTP lors de l'envoi du message : {e}")
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
        embed.set_author(
            name=stream_info['user_name'], icon_url=stream_info['profile_image_url'])
        embed.set_thumbnail(
            url=stream_info['thumbnail_url'].format(width=320, height=180))
        embed.add_field(
            name="Jeu", value=stream_info['game_name'], inline=False)
        embed.add_field(
            name="Vues", value=stream_info['viewer_count'], inline=False)
        embed.set_footer(text="Regardez le stream maintenant !")
        try:
            await channel.send(embed=embed)
            stream_cache.add(stream_info['id'])
        except discord.errors.Forbidden:
            logging.error(
                f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
        except discord.errors.HTTPException as e:
            logging.error(f"Erreur HTTP lors de l'envoi du message : {e}")
        except Exception as e:
            logging.error(f"Erreur inattendue : {e}")


async def check_news():
    await client.wait_until_ready()
    while True:
        news_items = await fetch_swtor_news()
        await send_news_to_channel(CHANNEL_ID, news_items)
        # Attendre 1 heure avant de récupérer les news à nouveau
        await asyncio.sleep(3600)


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
    # client.loop.create_task(check_news())
    # client.loop.create_task(check_streams())

# Welcome

# Configurer le logging
logging.basicConfig(level=logging.INFO)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les variables d'environnement
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SOCIAL_ID = int(os.getenv('SOCIAL_ID'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
OTHER_BOT_COMMAND = os.getenv('OTHER_BOT_COMMAND')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_USERNAME = os.getenv('TWITCH_USERNAME')
# Chemin vers l'image de fond locale
WELCOME_IMAGE_PATH = os.getenv('WELCOME_IMAGE_PATH')
FONT_PATH = os.getenv('FONT_PATH')  # Chemin vers le fichier de police

intents = discord.Intents.default()
intents.members = True  # Activer l'intention pour détecter les membres
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
        news_items.append({'title': title, 'description': description,
                          'link': full_link, 'image_url': image_url})

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
                embed.set_footer(text="SWTOR News",
                                 icon_url="https://www.swtor.com/favicon.ico")
                if item['image_url']:
                    embed.set_image(url=item['image_url'])
                embed.add_field(
                    name="Lien", value=f"[Lire plus]({item['link']})", inline=False)
                try:
                    await channel.send(embed=embed)
                    news_cache.add(item['link'])
                except discord.errors.Forbidden:
                    logging.error(
                        f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
                except discord.errors.HTTPException as e:
                    logging.error(
                        f"Erreur HTTP lors de l'envoi du message : {e}")
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
        embed.set_author(
            name=stream_info['user_name'], icon_url=stream_info['profile_image_url'])
        embed.set_thumbnail(
            url=stream_info['thumbnail_url'].format(width=320, height=180))
        embed.add_field(
            name="Jeu", value=stream_info['game_name'], inline=False)
        embed.add_field(
            name="Vues", value=stream_info['viewer_count'], inline=False)
        embed.set_footer(text="Regardez le stream maintenant !")
        try:
            await channel.send(embed=embed)
            stream_cache.add(stream_info['id'])
        except discord.errors.Forbidden:
            logging.error(
                f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
        except discord.errors.HTTPException as e:
            logging.error(f"Erreur HTTP lors de l'envoi du message : {e}")
        except Exception as e:
            logging.error(f"Erreur inattendue : {e}")


async def check_news():
    await client.wait_until_ready()
    while True:
        news_items = await fetch_swtor_news()
        await send_news_to_channel(CHANNEL_ID, news_items)
        # Attendre 1 heure avant de récupérer les news à nouveau
        await asyncio.sleep(3600)


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
    # client.loop.create_task(check_news())
    # client.loop.create_task(check_streams())


@client.event
async def on_member_join(member):
    channel = client.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        # Vérifier si le fichier de police existe
        if os.path.exists(FONT_PATH):
            logging.info(
                f"Le fichier de police a été trouvé à l'emplacement : {FONT_PATH}")
            # Créer une image personnalisée avec un arrière-plan et du texte
            background = Image.open(WELCOME_IMAGE_PATH)
            draw = ImageDraw.Draw(background)
            # Vous pouvez changer la police et la taille
            font = ImageFont.truetype(FONT_PATH, 40)

            # Ajouter du texte à l'image
            welcome_text = f"Bienvenue {member.name} !"
            bbox = draw.textbbox((0, 0), welcome_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            width, height = background.size
            x = (width - text_width) / 2
            y = (height - text_height) / 2
            draw.text((x, y), welcome_text, font=font, fill="white")

            # Sauvegarder l'image dans un objet BytesIO
            buffer = BytesIO()
            background.save(buffer, format="PNG")
            buffer.seek(0)

            # Créer un objet discord.File à partir de l'image
            file = discord.File(buffer, filename="welcome_image.png")

            # Créer l'embed de bienvenue
            embed = discord.Embed(
                title=f"Bienvenue {member.name} !",
                description=f"Bienvenue sur le serveur, {member.mention} ! Nous sommes ravis de t'avoir parmi nous.",
                color=discord.Color.green()
            )
            embed.set_thumbnail(
                url=member.avatar.url if member.avatar else "https://via.placeholder.com/150")
            embed.set_image(url=f"attachment://{file.filename}")
            embed.add_field(name="Nom d'utilisateur",
                            value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Date de création du compte", value=member.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"), inline=False)
            embed.set_footer(text="Amuse-toi bien sur le serveur !")

            try:
                await channel.send(file=file, embed=embed)
            except discord.errors.Forbidden:
                logging.error(
                    f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {WELCOME_CHANNEL_ID}.")
            except discord.errors.HTTPException as e:
                logging.error(f"Erreur HTTP lors de l'envoi du message : {e}")
            except Exception as e:
                logging.error(f"Erreur inattendue : {e}")
        else:
            logging.error(
                f"Le fichier de police n'a pas été trouvé à l'emplacement : {FONT_PATH}")

# keep_alive()
client.run(TOKEN)
