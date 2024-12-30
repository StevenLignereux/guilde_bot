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
        self.check_news.start()

    async def fetch_swtor_news(self):
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
            news_items.append({'title': title, 'description': description,
                               'link': full_link, 'image_url': image_url})

        return news_items

    async def send_news_to_channel(self, channel, news_items):
        for item in news_items:
            if item['link'] not in self.news_cache:
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
                    self.news_cache.add(item['link'])
                except discord.errors.Forbidden:
                    logging.error(
                        f"Le bot n'a pas les permissions nécessaires pour envoyer des messages dans le canal {channel.id}.")
                except discord.errors.HTTPException as e:
                    logging.error(
                        f"Erreur HTTP lors de l'envoi du message : {e}")
                except Exception as e:
                    logging.error(f"Erreur inattendue : {e}")

    @commands.command(name='news')
    async def news_command(self, ctx):
        news_items = await self.fetch_swtor_news()
        await self.send_news_to_channel(ctx.channel, news_items)

    @tasks.loop(hours=1)
    async def check_news(self):
        channel_id = int(os.getenv('CHANNEL_ID'))
        channel = self.bot.get_channel(channel_id)
        if channel:
            news_items = await self.fetch_swtor_news()
            await self.send_news_to_channel(channel, news_items)

    @check_news.before_loop
    async def before_check_news(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(News(bot))
