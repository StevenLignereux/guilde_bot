import os
from aiohttp import web
import asyncio
from main import main as bot_main
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(_: web.Request):
    return web.Response(text="Bot is running")

async def start_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    port = int(os.environ["PORT"])
    logger.info(f"Démarrage du serveur sur le port {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"Serveur web démarré sur le port {port}")
    return runner

async def main():
    runner = await start_server()
    try:
        logger.info("Démarrage du bot Discord...")
        await bot_main()
        while True:
            await asyncio.sleep(3600)  # Attendre indéfiniment
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du bot: {e}")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 