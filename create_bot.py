import logging
from aiogram import  Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import settings

admins = [int(admin_id) for admin_id in settings.ADMINS]

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())
