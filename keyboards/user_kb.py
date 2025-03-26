from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

import settings


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


def restart_poll_fraud() -> types.ReplyKeyboardMarkup:
    kb_list = [
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


def after_start_menu() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text='📸К фотографиям!',
        url=settings.PHOTO_CHANNEL_URL)
    )
    return builder.as_markup()
