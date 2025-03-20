from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_menu() -> types.ReplyKeyboardMarkup:
    kb_list = [[types.KeyboardButton(text='/start')]]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def new_user_menu() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [
            types.KeyboardButton(
                text='Отправить свой номер',
                request_contact=True,
                callback_data='contact',
            )
        ]
    ]
    return types.ReplyKeyboardMarkup(
        keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True
    )


def make_menu() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [
            types.KeyboardButton(text='🎪Место проведения'),
            types.KeyboardButton(text='🕒Расписание'),
        ],
        [types.KeyboardButton(text='🌸НАЖМИ')],
        [types.KeyboardButton(text='💬Пройти опрос заново')],
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def create_qst_inline_kb(
        question_id: str, question: dict
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # add answer buttons
    for key, value in question['answers'].items():
        builder.row(
            types.InlineKeyboardButton(
                text=value,
                callback_data=f'{question_id}_{key}',
            )
        )
    # set keyboard  size
    builder.adjust(question['adjust'])
    return builder.as_markup()


def admin_menu() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [
            types.KeyboardButton(text='Результаты опроса'),
            types.KeyboardButton(text='Кто придет?'),
            types.KeyboardButton(text='Кто не придет?'),
            types.KeyboardButton(text='Остальные'),
        ],
        [
            types.KeyboardButton(text='Установить приветственное фото'),
            types.KeyboardButton(text='Статистика'),
            types.KeyboardButton(text='Оповестить пользователей')
        ]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def cancel_keyboard() -> types.ReplyKeyboardMarkup:
    kb_list = [
        [types.KeyboardButton(text='Отмена'), ]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
