import asyncio

from create_bot import bot, dp
from handlers import admin_handlers, user_handlers
from managers.redis_mgr import RedisManager


async def main():
    await set_settings()

    dp.include_routers(user_handlers.router, admin_handlers.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def set_settings():
    redis_manager = RedisManager()
    await redis_manager.set_def_settings()


if __name__ == '__main__':
    asyncio.run(main())
