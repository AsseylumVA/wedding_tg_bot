from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import TelegramObject


class IgnoreGroupsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject,
                       data: dict[str, any]):
        if data['event_chat'].type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return  # Пропускаем обработку
        return await handler(event, data)
