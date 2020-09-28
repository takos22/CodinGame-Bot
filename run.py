import asyncio

from core import Bot
from config import Config

async def main():
    bot = Bot()

    try:
        await bot.start(Config.TOKEN)
    except KeyboardInterrupt:
        await bot.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
