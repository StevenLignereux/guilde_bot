import discord
from discord.ext import commands
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'Bot connecté en tant que {self.bot.user}')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            logger.info(f"Nouveau membre détecté : {member.name} (ID: {member.id})")
            
            # Récupération du channel de bienvenue
            welcome_channel_id = os.getenv('WELCOME_CHANNEL_ID')
            if not welcome_channel_id:
                logger.error("WELCOME_CHANNEL_ID non défini dans les variables d'environnement")
                return
                
            logger.debug(f"ID du canal de bienvenue : {welcome_channel_id}")
            channel = self.bot.get_channel(int(welcome_channel_id))
            
            if not channel:
                logger.error(f"Impossible de trouver le canal avec l'ID {welcome_channel_id}")
                return

            # Vérification des chemins des ressources
            font_path = os.getenv('FONT_PATH')
            welcome_image_path = os.getenv('WELCOME_IMAGE_PATH')
            
            if not font_path or not os.path.exists(font_path):
                logger.error(f"Fichier de police introuvable : {font_path}")
                return
                
            if not welcome_image_path or not os.path.exists(welcome_image_path):
                logger.error(f"Image de fond introuvable : {welcome_image_path}")
                return
                
            logger.debug("Ressources trouvées, création de l'image...")

            # Création de l'image de bienvenue
            background = Image.open(welcome_image_path)
            draw = ImageDraw.Draw(background)
            
            # Téléchargement et redimensionnement de l'avatar
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            logger.debug(f"URL de l'avatar : {avatar_url}")
            
            response = requests.get(avatar_url)
            avatar_image = Image.open(BytesIO(response.content))

            avatar_size = 475
            avatar_image = avatar_image.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

            # Création du masque circulaire
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

            # Application du masque
            avatar_image.putalpha(mask)

            # Position de l'avatar
            avatar_position = (60, 70)
            background.paste(avatar_image, avatar_position, avatar_image)

            # Ajout du texte
            welcome_text = f"Bienvenue \nsur le serveur discord \nLa Flotte exilée !"
            font_size = 110
            font = ImageFont.truetype(str(font_path), font_size)

            # Ajustement de la taille du texte
            bbox = draw.textbbox((0, 0), welcome_text, font=font, align="center")
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            while text_width > background.width - 20 or text_height > background.height - 20:
                font_size -= 1
                font = ImageFont.truetype(str(font_path), font_size)
                bbox = draw.textbbox((0, 0), welcome_text, font=font, align="center")
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

            # Position du texte
            x = avatar_position[0] + avatar_size + 130
            y = (background.height - text_height) / 2

            logger.debug("Ajout des effets de texte...")

            # Ajout de la bordure
            border_color = "black"
            border_size = 2
            for dx in range(-border_size, border_size + 1):
                for dy in range(-border_size, border_size + 1):
                    draw.text((x + dx, y + dy), welcome_text, font=font, fill=border_color, align="center")

            # Texte principal
            draw.text((x, y), welcome_text, font=font, fill="white", align="center")

            # Ombre du texte
            shadow_color = "#fefaf9"
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), welcome_text, font=font, fill=shadow_color, align="center")

            # Sauvegarde et envoi
            output_path = f"welcome_{member.id}.png"
            logger.debug(f"Sauvegarde de l'image : {output_path}")
            background.save(output_path)

            try:
                logger.debug("Envoi du message de bienvenue...")
                with open(output_path, 'rb') as f:
                    picture = discord.File(f)
                    await channel.send(file=picture)
                logger.info(f"Message de bienvenue envoyé avec succès pour {member.name}")
            finally:
                if os.path.exists(output_path):
                    os.remove(output_path)
                    logger.debug("Fichier temporaire supprimé")

        except Exception as e:
            logger.error(f"Erreur lors de la création du message de bienvenue : {str(e)}", exc_info=True)
            try:
                await channel.send(f"Bienvenue {member.mention} sur le serveur !")
            except:
                logger.error("Impossible d'envoyer le message de bienvenue de secours", exc_info=True)

async def setup(bot):
    await bot.add_cog(Events(bot))
