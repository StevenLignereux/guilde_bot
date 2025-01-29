import discord
from discord.ext import commands
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import sys

# Configuration du logger pour afficher dans la console
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)  # Définir le niveau à DEBUG pour voir tous les logs

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("\n=== Events Cog - Vérification des intents ===")
        print(f"Members Intent: {bot.intents.members}")
        print(f"Message Content Intent: {bot.intents.message_content}")
        print(f"Guilds Intent: {bot.intents.guilds}")
        
        if not bot.intents.members:
            print("❌ ERREUR: L'intent MEMBERS n'est pas activé!")
            return
            
        print("✅ Tous les intents nécessaires sont activés")
        print("\n=== Events Cog - Vérification des variables d'environnement ===")
        
        # Vérification des ressources au démarrage
        welcome_channel_id = os.getenv('WELCOME_CHANNEL_ID', '')
        font_path = os.getenv('FONT_PATH', '')
        welcome_image_path = os.getenv('WELCOME_IMAGE_PATH', '')
        
        print("=== Vérification de la configuration ===")
        print(f"Canal de bienvenue : {welcome_channel_id}")
        print(f"Chemin de la police : {font_path}")
        print(f"Chemin de l'image : {welcome_image_path}")
        
        # Vérifier si les fichiers existent
        if font_path and os.path.exists(font_path):
            print(f"✅ Police trouvée : {font_path}")
        else:
            print(f"❌ Police manquante : {font_path}")
            
        if welcome_image_path and os.path.exists(welcome_image_path):
            print(f"✅ Image trouvée : {welcome_image_path}")
        else:
            print(f"❌ Image manquante : {welcome_image_path}")
            
        # Afficher le contenu des dossiers
        print("\nContenu des dossiers de ressources :")
        os.system("ls -la src/resources/images/")
        os.system("ls -la src/resources/fonts/")
            
        print("=== Fin de la vérification ===")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"=== Bot prêt : {self.bot.user} ===")
        logger.info(f'Bot connecté en tant que {self.bot.user}')
        
        # Vérifier si le canal de bienvenue est accessible
        welcome_channel_id = os.getenv('WELCOME_CHANNEL_ID')
        if welcome_channel_id:
            channel = self.bot.get_channel(int(welcome_channel_id))
            if channel:
                print(f"✅ Canal de bienvenue trouvé : {channel.name}")
            else:
                print(f"❌ Canal de bienvenue introuvable : ID {welcome_channel_id}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"=== Nouveau membre rejoint : {member.name} ===")
        try:
            logger.info(f"Nouveau membre détecté : {member.name} (ID: {member.id})")
            
            # Récupération du channel de bienvenue
            welcome_channel_id = os.getenv('WELCOME_CHANNEL_ID')
            print(f"Channel ID configuré : {welcome_channel_id}")
            
            if not welcome_channel_id:
                print("ERREUR: WELCOME_CHANNEL_ID non défini")
                logger.error("WELCOME_CHANNEL_ID non défini dans les variables d'environnement")
                return
                
            logger.debug(f"ID du canal de bienvenue : {welcome_channel_id}")
            channel = self.bot.get_channel(int(welcome_channel_id))
            
            if not channel:
                print(f"ERREUR: Canal {welcome_channel_id} introuvable")
                logger.error(f"Impossible de trouver le canal avec l'ID {welcome_channel_id}")
                return

            # Vérification des chemins des ressources
            font_path = os.getenv('FONT_PATH')
            welcome_image_path = os.getenv('WELCOME_IMAGE_PATH')
            
            print(f"Chemins des ressources :")
            print(f"- Font : {font_path}")
            print(f"- Image : {welcome_image_path}")
            
            # Vérification détaillée des fichiers
            for path in [welcome_image_path, font_path]:
                if not path:  # Vérifier si le chemin est None ou vide
                    print(f"❌ Chemin non défini")
                    return
                    
                if not os.path.exists(path):
                    print(f"❌ Fichier manquant : {path}")
                    return
                    
                try:
                    # Vérifier les permissions
                    stats = os.stat(path)
                    print(f"Permissions pour {path}: {oct(stats.st_mode)[-3:]}")
                    # Vérifier si on peut lire le fichier
                    with open(str(path), 'rb') as f:
                        f.read(1)
                    print(f"✅ Fichier accessible : {path}")
                except Exception as e:
                    print(f"❌ Erreur d'accès au fichier {path}: {str(e)}")
                    logger.error(f"Erreur d'accès au fichier {path}: {str(e)}")
                    return
            
            print("Ressources validées, création de l'image...")
            
            try:
                # Création de l'image de bienvenue
                if not isinstance(welcome_image_path, str):
                    raise ValueError("Le chemin de l'image n'est pas une chaîne valide")
                background = Image.open(welcome_image_path)
                print("✅ Image de fond chargée")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de l'image de fond : {str(e)}")
                return
                
            try:
                # Chargement de la police
                font = ImageFont.truetype(str(font_path), 110)
                print("✅ Police chargée")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de la police : {str(e)}")
                return

            draw = ImageDraw.Draw(background)
            
            # Téléchargement et redimensionnement de l'avatar
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            print(f"URL de l'avatar : {avatar_url}")
            
            try:
                response = requests.get(avatar_url)
                response.raise_for_status()  # Vérifie si la requête a réussi
                avatar_image = Image.open(BytesIO(response.content))
                print("✅ Avatar téléchargé")
            except Exception as e:
                print(f"❌ Erreur lors du téléchargement de l'avatar : {str(e)}")
                return

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

            print("Création du texte et des effets...")

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
            output_path = f"/tmp/welcome_{member.id}.png"  # Utiliser /tmp pour être sûr d'avoir les permissions
            print(f"Tentative de sauvegarde de l'image : {output_path}")
            try:
                background.save(output_path)
                print(f"✅ Image sauvegardée : {output_path}")
                
                print(f"Vérification du fichier sauvegardé...")
                if os.path.exists(output_path):
                    print(f"✅ Fichier trouvé : {output_path}")
                    file_size = os.path.getsize(output_path)
                    print(f"Taille du fichier : {file_size} bytes")
                else:
                    print(f"❌ Fichier non trouvé après sauvegarde : {output_path}")
                    return

                print("Tentative d'envoi du message...")
                with open(output_path, 'rb') as f:
                    picture = discord.File(f, filename="welcome.png")
                    await channel.send(file=picture)
                print(f"✅ Message envoyé avec succès pour {member.name}")
                
            except Exception as e:
                print(f"❌ ERREUR lors de la sauvegarde/envoi : {str(e)}")
                logger.error(f"Erreur détaillée : {str(e)}", exc_info=True)
                return
            finally:
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                        print("✅ Fichier temporaire supprimé")
                except Exception as e:
                    print(f"❌ Erreur lors de la suppression du fichier temporaire : {str(e)}")
                    pass

        except Exception as e:
            print(f"ERREUR: {str(e)}")
            logger.error(f"Erreur lors de la création du message de bienvenue : {str(e)}", exc_info=True)
            try:
                await channel.send(f"Bienvenue {member.mention} sur le serveur !")
            except Exception as e:
                print(f"ERREUR lors de l'envoi du message de secours : {str(e)}")
                logger.error("Impossible d'envoyer le message de bienvenue de secours", exc_info=True)

async def setup(bot):
    await bot.add_cog(Events(bot))
    print("=== Events Cog chargé ===")
