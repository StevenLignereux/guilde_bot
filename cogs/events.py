import discord
from discord.ext import commands
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Connecté en tant que {self.bot.user}')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(int(os.getenv('WELCOME_CHANNEL_ID')))
        if channel:
            # Vérifier si le fichier de police existe
            font_path = os.getenv('FONT_PATH')
            if os.path.exists(font_path):
                logging.info(
                    f"Le fichier de police a été trouvé à l'emplacement : {font_path}")
                # Créer une image personnalisée avec un arrière-plan et du texte
                background = Image.open(os.getenv('WELCOME_IMAGE_PATH'))
                draw = ImageDraw.Draw(background)
                # Vous pouvez changer la police et la taille
                font = ImageFont.truetype(font_path, 100)

                # Charger l'avatar de l'utilisateur
                avatar_url = member.avatar.url if member.avatar else "https://via.placeholder.com/150"
                response = requests.get(avatar_url)
                avatar_image = Image.open(BytesIO(response.content))

                avatar_size = 475  # Taille souhaitée pour l'avatar
            avatar_image = avatar_image.resize(
                (avatar_size, avatar_size), Image.LANCZOS)

            # Créer un masque circulaire
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

            # Appliquer le masque à l'avatar
            avatar_image.putalpha(mask)

            # Position de l'avatar sur l'image de fond
            # Coordonnées (x, y) pour placer l'avatar
            avatar_position = (60, 70)
            background.paste(avatar_image, avatar_position, avatar_image)

            # Ajouter du texte à l'image
            welcome_text = f"Bienvenue \nsur le serveur discord \nLa Flotte exilée !"
            font_size = 110  # Taille initiale de la police
            font = ImageFont.truetype(font_path, font_size)

            # Ajuster la taille de la police en fonction de la taille du texte
            bbox = draw.textbbox((0, 0), welcome_text,
                                 font=font, align="center")
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            while text_width > background.width - 20 or text_height > background.height - 20:
                font_size -= 1
                font = ImageFont.truetype(font_path, font_size)
                bbox = draw.textbbox((0, 0), welcome_text,
                                     font=font, align="center")
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

            # Calculer les coordonnées pour positionner le texte à gauche de l'avatar
            x = avatar_position[0] + avatar_size + 130
            y = (background.height - text_height) / 2
            draw.text((x, y), welcome_text, font=font,
                      fill="white", align="center")

            # Ajouter une bordure au texte
            border_color = "black"
            border_size = 2
            for dx in range(-border_size, border_size + 1):
                for dy in range(-border_size, border_size + 1):
                    draw.text((x + dx, y + dy), welcome_text,
                              font=font, fill=border_color, align="center")

            # Ajouter une ombre au texte
            shadow_color = "#fefaf9"
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset),
                      welcome_text, font=font, fill=shadow_color, align="center")

            # Sauvegarder l'image
            output_path = f"welcome_{member.id}.png"
            background.save(output_path)

            # Envoyer l'image dans le canal de bienvenue
            with open(output_path, 'rb') as f:
                picture = discord.File(f)
                await channel.send(file=picture)


async def setup(bot):
    await bot.add_cog(Events(bot))
