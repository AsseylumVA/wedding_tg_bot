import logging
from logging.handlers import TimedRotatingFileHandler

from aiogram import Router, F, types

from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import settings

router = Router()

log_format = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[TimedRotatingFileHandler(settings.LOG_FILE, when='d')],
)

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
            {'text': '🍺Тёмное пиво', 'value': 'lightbeer'},
            {'text': '🍻Светлое пиво', 'value': 'darkbeer'},
        ],
        'adjust': 2,
    },
}


class UserState(StatesGroup):
    NEW_USER = State()
    REGISTERED = State()
    FRAUD = State()
    WAITING_FOR_ANSWERS = State()


def start_menu():
    kb_list = [[types.KeyboardButton(text='/start')]]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb_list, resize_keyboard=True
    )
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
        [
            types.KeyboardButton(text='Расписание'),
            types.KeyboardButton(text='Место проведения'),
        ],
        [types.KeyboardButton(text='Информация')],
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


def create_qst_inline_kb(
    question_id: int, question: dict
) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # add answer buttons
    for answer in question['answers']:
        builder.row(
            types.InlineKeyboardButton(
                text=answer['text'],
                callback_data=f'qst_{question_id}_{answer["value"]}',
            )
        )
    # set keyboard  size
    builder.adjust(question['adjust'])
    return builder.as_markup()


@router.message(StateFilter(None), CommandStart())
async def start_new_user(message: Message, state: FSMContext):
    """
    This handler will be called when user sends `/start` or `/help` command
    """

    await message.answer(
        'Мы еще не знакомы. Пожалуйста, представься',
        reply_markup=new_user_menu(),
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
    await state.set_state(UserState.WAITING_FOR_ANSWERS)
    question_id = 1
    question = questions[question_id]
    await message.answer(
        text=question['text'],
        reply_markup=create_qst_inline_kb(question_id, question),
    )


@router.callback_query(
    StateFilter(UserState.WAITING_FOR_ANSWERS), F.data.startswith('qst_')
)
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

    if question_id == 1 and answer_value == 'False':
        await callback.message.answer(
            'Очень жаль, что ты не сможешь прийти. 😢'
        )
        await state.set_state(UserState.FRAUD)
        return

    # Отправляем следующий вопрос (если есть)
    next_question_id = question_id + 1
    if next_question_id in questions:
        next_question = questions[next_question_id]
        await callback.message.answer(
            text=next_question['text'],
            reply_markup=create_qst_inline_kb(next_question_id, next_question),
        )
    else:
        await state.set_state(UserState.REGISTERED)
        await callback.message.answer(
            'Спасибо за ответы! 🎉', reply_markup=make_menu()
        )


async def process_answer(
    state: FSMContext,
    answer_value: str,
    question_id: int,
):
    # Сохраняем ответ в состоянии
    await state.update_data({question_id: answer_value})


@router.message(F.text)
async def unknown_command(message: types.Message, state: FSMContext):
    logging.error(f'unknown user state: {state}')

    if state == UserState.FRAUD:
        await message.answer('Очень жаль, что ты не сможешь прийти. 😢')
        return

    if state is not None:
        reply_markup = None
        if state == UserState.REGISTERED:
            reply_markup = make_menu()

        await message.answer(
            'Доступны только команды из меню', reply_markup=reply_markup
        )
        return

    await message.answer('Мы не знакомы', reply_markup=start_menu())
