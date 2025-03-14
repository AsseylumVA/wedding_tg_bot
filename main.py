import logging
from logging.handlers import TimedRotatingFileHandler

from aiogram import Bot, Router, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import settings

bot = Bot(
    token=settings.API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
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


# Словарь вопросов
questions = {
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
            {'text': '🍺Тёмное пиво', 'value': 'light_beer'},
            {'text': '🍻Светлое пиво', 'value': 'dark_beer'},
        ],
        'adjust': 2,
    },
}


class UserState(StatesGroup):
    NEW_USER = State()
    REGISTERED = State()
    FRAUD = State()
    LAST_STEP = State()


def start_menu():
    kb_list = [[types.KeyboardButton(text='/start')]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)
    return keyboard


def new_user_menu():
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


def make_menu():
    kb_list = [
        [types.KeyboardButton(text='Расписание'), types.KeyboardButton(text='Место проведения')],
        [types.KeyboardButton(text='Информация')],
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def create_qst_inline_kb(
    question_id: int, question: dict
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Добавляем кнопки вопросов
    for answer in question['answers']:
        builder.row(
            types.InlineKeyboardButton(
                text=answer['text'],
                callback_data=f'qst_{question_id}_{answer["value"]}',
            )
        )
    # Настраиваем размер клавиатуры
    builder.adjust(question['adjust'])
    return builder.as_markup()


@router.message(StateFilter(None), CommandStart())
async def start_new_user(message: Message, state: FSMContext):
    """
    This handler will be called when user sends `/start` or `/help` command
    """

    await message.answer(
        'Мы еще не знакомы. Пожалуйста, представься', reply_markup=new_user_menu()
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
    question_id = 1
    question = questions[question_id]
    await message.answer(
        text=question['text'],
        reply_markup=create_qst_inline_kb(question_id, question),
    )

@router.callback_query(StateFilter(UserState.REGISTERED), F.data.startswith('qst_'))
async def handle_q_answers(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Разбираем callback_data
    _, question_id, answer_value = callback.data.split('_')
    question_id = int(question_id)

    # Получаем вопрос из словаря
    question = questions.get(question_id)
    if not question:
        await callback.answer('Ошибка: вопрос не найден.')
        return

    await process_answer(state, answer_value, question_id)

    # Отправляем следующий вопрос (если есть)
    next_question_id = question_id + 1
    if next_question_id in questions:
        next_question = questions[next_question_id]
        await callback.message.answer(
            text=next_question['text'],
            reply_markup=create_qst_inline_kb(next_question_id, next_question),
        )
    else:
        state.set_state(UserState.LAST_STEP)
        await callback.message.answer('Спасибо за ответы! 🎉', reply_markup=make_menu())


async def process_answer(
    state: FSMContext,
    answer_value: str,
    question_id: int,
):
    # Сохраняем ответ в состоянии
    await state.update_data({question_id: answer_value})
