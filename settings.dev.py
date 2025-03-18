# Токен для подключени бота к Telegram
API_TOKEN = 'CHANGEME'
LOG_FILE = 'wedding_bot.log'
ADMINS = {}

"""
база данных номеров
Пример:
db = {
    '+79999999999': {
        'name': 'Петр',
    }
}
"""
DB = {}

QUESTIONS = {
    1: {
        'id': 1,
        'text': 'Планируешь ли ты посетить нашу свадьбу?',
        'answers': [
            {'text': '🎉Да', 'value': True},
            {'text': '😕Нет', 'value': False},
        ],
        'adjust': 2,
    },
    2: {
        'text': 'Нужен ли тебе трансфер?',
        'answers': [
            {'text': '🚌Да', 'value': True},
            {'text': '🚕Нет, приеду сам(а)', 'value': False},
        ],
        'adjust': 2,
    },
    3: {
        'text': 'Какой алкоголь предпочитаешь?',
        'answers': [
            {'text': '🍸Крепкий', 'value': 'hard'},
            {'text': '🍷Вино', 'value': 'wine'},
            {'text': '🍺Тёмное пиво', 'value': 'lightbeer'},
            {'text': '🍻Светлое пиво', 'value': 'darkbeer'},
        ],
        'adjust': 2,
    },
}
