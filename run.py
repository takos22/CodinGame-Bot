import asyncio

from bot import CodinGameBot
from config import Config

async def main():
    bot = CodinGameBot()

    try:
        await bot.start(Config.TOKEN)
    except Exception as exc:
        try:
            await bot.handle_error(exc)
        except Exception:
            pass
    finally:
        await bot.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
