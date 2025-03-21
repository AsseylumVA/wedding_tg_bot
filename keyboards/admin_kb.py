from aiogram import types


def admin_menu() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [
            types.KeyboardButton(text='Результаты опроса'),
            types.KeyboardButton(text='Кто придет?'),
            types.KeyboardButton(text='Кто не придет?'),
            types.KeyboardButton(text='Остальные'),
        ],
        [
            types.KeyboardButton(text='Статистика'),
        ],
        [
            types.KeyboardButton(text='Оповестить пользователей'),
            types.KeyboardButton(text='Настройка картинок'),
        ]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def cancel_keyboard() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [types.KeyboardButton(text='Отмена'), ]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def return_keyboard() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [types.KeyboardButton(text='Назад'), ]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)

def set_photos() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [
            types.KeyboardButton(text='Приветственное фото'),
            types.KeyboardButton(text='Фото дресс кода')
        ]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)