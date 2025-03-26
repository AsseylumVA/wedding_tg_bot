import asyncio

from create_bot import bot, dp
from handlers import admin_handlers, user_handlers
from managers.message_sender import MessageScheduler
from managers.redis_mgr import RedisManager
from middlewares import IgnoreGroupsMiddleware


async def main():
    redis_manager = RedisManager()
    await redis_manager.set_def_settings()

    scheduler = MessageScheduler(bot, redis_manager)
    asyncio.create_task(scheduler.run())

    await bot.delete_webhook(drop_pending_updates=True)

    dp["bot"] = bot
    dp.include_routers(user_handlers.router, admin_handlers.router)
    dp.update.outer_middleware(IgnoreGroupsMiddleware())
    await dp.start_polling(bot)


async def set_settings():
    redis_manager = RedisManager()
    await redis_manager.set_def_settings()


if __name__ == '__main__':
    asyncio.run(main())
