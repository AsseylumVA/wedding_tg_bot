import asyncio

from create_bot import bot, dp
from handlers import admin_handlers, user_handlers


async def main():
    dp.include_routers(user_handlers.router, admin_handlers.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
