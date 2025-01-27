import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import os
import logging



class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = requests.Session()
        self.news_cache = set()
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Démarrer la tâche de vérification des news une fois que le bot est prêt"""
        self.check_news.start()

    def cog_unload(self):
        """Arrêter la tâche quand le cog est déchargé"""
        self.check_news.cancel()

    @tasks.loop(minutes=30)
    async def check_news(self):
        """Vérifie les nouvelles de SWTOR toutes les 30 minutes"""
        try:
            news_items = await self.fetch_swtor_news()
            await self.send_news_to_channel(news_items)
        except Exception as e:
            logging.error(f"Erreur lors de la vérification des news : {str(e)}")

    async def fetch_swtor_news(self):
        """Récupère les dernières nouvelles de SWTOR"""
        url = 'https://www.swtor.com/fr/info/news'
        response = self.session.get(url)
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
            news_items.append({
                'title': title,
                'description': description,
                'link': full_link,
                'image_url': image_url
            })

        return news_items

    async def send_news_to_channel(self, news_items):
        """Envoie les nouvelles dans le canal approprié"""
        if not news_items:
            return

        channel_id = int(os.getenv('NEWS_CHANNEL_ID'))
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            logging.error(f"Canal des news non trouvé (ID: {channel_id})")
            return

        for news in news_items:
            if news['link'] not in self.news_cache:
                embed = discord.Embed(
                    title=news['title'],
                    description=news['description'],
                    url=news['link'],
                    color=discord.Color.blue()
                )
                
                if news['image_url']:
                    embed.set_image(url=news['image_url'])
                
                await channel.send(embed=embed)
                self.news_cache.add(news['link'])

async def setup(bot):
    await bot.add_cog(News(bot))
