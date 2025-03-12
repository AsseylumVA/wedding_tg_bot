import logging
from logging.handlers import TimedRotatingFileHandler

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message

import settings

router = Router()

log_format = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[TimedRotatingFileHandler(settings.LOG_FILE, when='d')],
)


# @start_router.message(CommandStart())
# async def cmd_start(message: Message):
#     await message.answer('Запуск сообщения по команде /start используя фильтр CommandStart()')

# @start_router.message(Command('start_2'))
# async def cmd_start_2(message: Message):
#     await message.answer('Запуск сообщения по команде /start_2 используя фильтр Command()')

# @start_router.message(F.text == '/start_3')
# async def cmd_start_3(message: Message):
#     await message.answer('Запуск сообщения по команде /start_3 используя магический фильтр F.text!')


class UserState(StatesGroup):
    NEW_USER = State()
    REGISTERED = State()
    FRAUD = State()


def start_menu():
    kb_list = [[types.KeyboardButton(text='/start')]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard


def make_menu():
    kb_list = [[types.KeyboardButton(text='test')]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard


@router.message(StateFilter(None), CommandStart())
async def start_new_user(message: Message, state: FSMContext):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    kb_list = [
        [
            types.KeyboardButton(
                text='Отправить свой номер',
                request_contact=True,
                callback_data='contact',
            )
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer(
        'Мы еще не знакомы. Пожалуйста, представься', reply_markup=keyboard
    )
    return

@router.message(F.contact)
async def register(message: types.Message, state: FSMContext):
    await state.clear()

    if message.contact.user_id != message.from_user.id:
        await message.answer('Не пытайся меня обмануть')
        return

    phone_number = message.contact.phone_number
    if not phone_number.startswith('+'):
        phone_number = f'+{phone_number}'

    user_data = settings.DB.get(phone_number)
    if not user_data:
        data = await state.get_data()
        data['fraud'] = data.setdefault('fraud', 0) + 1
        await state.update_data(data)
        await message.answer(
            'Я тебя не знаю. Если ты считаешь это ошибкой, '
            'обратись к системному администратору.'
        )
        return

    await state.update_data(user_data)
    await state.set_state(UserState.REGISTERED)
    await message.answer(f'Привет, {user_data["name"]}!', reply_markup=make_menu())
