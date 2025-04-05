import asyncio
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from aiogram import Bot

import settings
from managers.redis_mgr import RedisManager

logging.basicConfig(
    level=logging.INFO,
    format=settings.LOG_FORMAT,
    handlers=[TimedRotatingFileHandler(settings.LOG_FILE, when='d')],
)
logger = logging.getLogger(__name__)


async def get_current_time():
    return datetime.now(settings.TZ)


class MessageSenderManager:
    def __init__(self, bot):
        self.redis_manager = RedisManager()
        self.bot = bot

    async def send_messages(self, message_text, reply_markup=None):
        user_keys = await self.redis_manager.get_all_users()
        for user_key in user_keys:
            try:
                user_id = user_key.replace('user:', '')
                await self.bot.send_message(chat_id=user_id, text=message_text,
                                            reply_markup=reply_markup)
                await asyncio.sleep(0.3)  # Anti-flood
            except Exception as e:
                logger.error(f"Ошибка отправки для {user_id}: {e}")

    async def send_welcome_messages(self, user_id):
        now = await get_current_time()
        for msg_name, msg_data in settings.SCHEDULED_MESSAGES.items():
            if msg_data['send_time'] <= now:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=msg_data['text'],
                        reply_markup=msg_data['reply_markup']
                    )
                    await asyncio.sleep(0.3)  # Anti-flood
                except Exception as e:
                    logger.error(
                        f"Ошибка отправки {msg_name} для {user_id}: {str(e)}")
                    continue


class MessageScheduler:
    def __init__(self, bot: Bot, redis_manager: RedisManager):
        self.bot = bot
        self.redis_manager = redis_manager
        self.sender = MessageSenderManager(bot)
        self.tasks = []

    async def check_and_send(self):
        """Проверяет и отправляет запланированные сообщения"""
        logger.info('Рассылка начата')
        messages_to_send = settings.SCHEDULED_MESSAGES.copy()
        while messages_to_send:
            now = await get_current_time()
            for msg_name, msg_data in list(messages_to_send.items()):
                if msg_data['send_time'] <= now:
                    await self.sender.send_messages(msg_data['text'],
                                                    msg_data['reply_markup'])
                    logger.info(f'Сообщение отправлено: {msg_name}')
                    messages_to_send.pop(msg_name)
                    # Задержка для защиты от флуда
                    await asyncio.sleep(0.3)
            await asyncio.sleep(60)
        logger.info('Все запланированные сообщения отправлены')

    async def run(self):
        """Запускает все задачи рассылки"""
        self.tasks.append(asyncio.create_task(self.check_and_send()))
