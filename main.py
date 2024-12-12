import discord
import requests
from bs4 import BeautifulSoup
import asyncio
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les variables d'environnement
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def fetch_swtor_news():
    url = 'https://www.swtor.com/fr/info/news'
    response = requests.get(url)
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
            except discord.errors.Forbidden:
                print(f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel_id}.")
            except discord.errors.HTTPException as e:
                print(f"Erreur HTTP lors de l'envoi du message : {e}")
            except Exception as e:
                print(f"Erreur inattendue : {e}")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    while True:
        news_items = await fetch_swtor_news()
        await send_news_to_channel(CHANNEL_ID, news_items)
        await asyncio.sleep(60)  # Attendre 1 heure avant de récupérer les news à nouveau

client.run(TOKEN)
