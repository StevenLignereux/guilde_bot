import os
from aiohttp import web
import asyncio
from main import main as bot_main

async def health_check(request):
    return web.Response(text="Bot is running")

async def start_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Server started on port {port}")

async def start_application():
    # Démarrer le serveur web et le bot en parallèle
    await asyncio.gather(
        start_server(),
        bot_main()
    )

if __name__ == "__main__":
    asyncio.run(start_application()) 