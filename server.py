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
    logger.info(f"Serveur démarré et à l'écoute sur le port {port}")

async def start_application():
    try:
        # Démarrer le serveur web et le bot en parallèle
        await asyncio.gather(
            start_server(),
            bot_main()
        )
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'application : {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Démarrage de l'application...")
    asyncio.run(start_application()) 