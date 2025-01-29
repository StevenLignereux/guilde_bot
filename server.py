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
        
        # Render s'attend à ce que nous utilisions la variable PORT
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"Configuration du serveur sur le port {port}")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=port)
        await site.start()
        logger.info(f"Serveur web démarré avec succès sur le port {port}")
        return site, runner
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur web : {str(e)}")
        raise

async def start_application():
    try:
        # Démarrer d'abord le serveur web
        site, runner = await start_server()
        logger.info("Serveur web initialisé, démarrage du bot...")
        
        # Ensuite démarrer le bot
        try:
            await bot_main()
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot : {str(e)}")
            raise
        finally:
            # S'assurer que le serveur web reste en cours d'exécution
            try:
                # Attendre indéfiniment
                await asyncio.Future()
            except asyncio.CancelledError:
                logger.info("Arrêt du serveur web...")
                await runner.cleanup()
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'application : {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Démarrage de l'application...")
    try:
        asyncio.run(start_application())
    except KeyboardInterrupt:
        logger.info("Arrêt de l'application...")
    except Exception as e:
        logger.error(f"Erreur critique : {str(e)}")
        raise 