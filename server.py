import os
from aiohttp import web
import asyncio
from main import main as bot_main
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="Bot is running")

async def start_server():
    try:
        app = web.Application()
        app.router.add_get("/", health_check)
        app.router.add_get("/health", health_check)
        
        # Forcer l'utilisation du port de Render
        port = int(os.getenv("PORT", 10000))
        logger.info(f"Configuration du serveur sur le port {port}")
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        # Spécifier explicitement l'hôte et le port
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        
        logger.info(f"Serveur web démarré sur http://0.0.0.0:{port}")
        return site, runner
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur web : {str(e)}")
        raise

async def start_application():
    try:
        # Démarrer le serveur web
        site, runner = await start_server()
        logger.info("Serveur web démarré, lancement du bot...")
        
        # Démarrer le bot dans une tâche séparée
        bot_task = asyncio.create_task(bot_main())
        
        # Attendre indéfiniment tout en gardant le serveur actif
        await asyncio.gather(
            bot_task,
            asyncio.Future()  # Garde le serveur web en vie
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'application : {str(e)}")
        raise
    finally:
        # Nettoyage
        if 'runner' in locals():
            await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(start_application())
    except KeyboardInterrupt:
        logger.info("Arrêt de l'application...")
    except Exception as e:
        logger.error(f"Erreur critique : {str(e)}")
        raise 