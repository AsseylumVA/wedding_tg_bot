import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import ReplyKeyboardRemove

from keyboards.user_kb import after_start_menu

TZ = ZoneInfo('Asia/Yekaterinburg')
LOG_FORMAT = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'

# Токен для подключения бота к Telegram
API_TOKEN = os.getenv('API_TOKEN')
PHOTO_CHANNEL_URL = os.getenv('PHOTO_CHANNEL_URL')

"""
база данных номеров
Пример:
db = {
    '+79999999999': {
        'name': 'Петр',
        'is_admin': 'False',
    }
}
"""
with open('DB.json', 'r', encoding='utf-8') as f:
    DB = json.load(f)

LOG_FILE = 'var/log/wedding_bot.log'

DEFAULT_FILE_ID = 'AgACAgIAAxkBAAIItWfhA1RGz-4QDSIDlSt_XfRJKVJjAAKB6DEbUFsJS8ZNTpbh9mGIAQADAgADeAADNgQ'

REDIS_DB = 'redis://redis_container:6379/1'
REDIS_USER_DATA_DB = 'redis://redis_container:6379/0'
START_TIME = datetime(2025, 6, 14, 12, 0, tzinfo=TZ)

"""
Отложенные сообщения
SCHEDULED_MESSAGES = {
    'new_event': {
        'text': 'Текст нового сообщения',
        'send_time': datetime(2025, 4, 1, 12, 0),  # 1 апреля 2025 в 12:00
    }
}
"""

SCHEDULED_MESSAGES = {
    'wedding': {
        'text': f'🎉Добро пожаловать на нашу свадьбу!',
        'send_time': START_TIME,
        'reply_markup': ReplyKeyboardRemove(),
    },
    'info': {
        'text': 'Кидайте фотки 🤖<b>БОТУ</b>\n'
                'Кадры с хештегом #️⃣<b>баттл</b> попадут в конкурс!\n',
        'send_time': START_TIME,
        'reply_markup': after_start_menu(),
    }
}
