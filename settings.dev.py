from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import ReplyKeyboardRemove

from keyboards.user_kb import after_start_menu

TZ = ZoneInfo('Asia/Yekaterinburg')
LOG_FORMAT = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'

# Токен для подключения бота к Telegram
API_TOKEN = ''
LOG_FILE = 'wedding_bot.log'
DEFAULT_FILE_ID = 'AgACAgIAAxkBAAIItWfhA1RGz-4QDSIDlSt_XfRJKVJjAAKB6DEbUFsJS8ZNTpbh9mGIAQADAgADeAADNgQ'

PHOTO_CHANNEL_URL = 'https://t.me/your_chat_username'

START_TIME = datetime(2025, 3, 26, 18, 7, tzinfo=TZ)

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
DB = {}

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
        'text': 'Теперь в этот чат вы можете скидывать фотки с нашего мероприятия!\n'
                'Фотографии отмеченные хештегом #баттл будут приняты к участию в конкурсе!\n'
                f'Все фотографии, которые вы скинете боту, будут опубликованы <a href="{PHOTO_CHANNEL_URL}">тут!</a>',
        'send_time': START_TIME,
        'reply_markup': after_start_menu(),
    }
}

REDIS_DB = 'redis://redis:6379/1'
REDIS_USER_DATA_DB = 'redis://redis:6379/0'
