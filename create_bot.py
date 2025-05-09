import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

storage = RedisStorage.from_url(settings.REDIS_DB)
dp = Dispatcher(storage=storage)
bot = Bot(
    token=settings.API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
