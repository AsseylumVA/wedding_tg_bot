# Токен для подключени бота к Telegram
API_TOKEN = 'CHANGEME'
LOG_FILE = 'wedding_bot.log'

"""
база данных номеров
Пример:
db = {
    '+79999999999': {
        'name': 'Петр',
        'is_admin': 'False',
        'full_name': 'Петров Петр',
    }
}
"""
DB = {}
REDIS_DB = 'redis://HOST:PORT/DB_NUM'
