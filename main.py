import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler

from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from redis.asyncio import Redis

import messages
import settings

router = Router()
redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

log_format = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[TimedRotatingFileHandler(settings.LOG_FILE, when='d')],
)


class UserState(StatesGroup):
    NEW_USER = State()
    REGISTERED = State()
    FRAUD = State()
    WAITING_FOR_ANSWERS = State()
    ADMIN = State()


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
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True)


async def process_answer(
        state: FSMContext,
        answer_value: str,
        question_id: str,
):
    # Сохраняем ответ в состоянии
    await state.update_data({f'{question_id}': answer_value})


async def save_answers_to_redis(user_data: dict):
    # Сохраняем все ответы в Redis
    name = user_data['name']
    for key, value in user_data.items():
        if not key.startswith('qst_'):
            continue
        await redis_client.hset(f'user:{name}', key, value)


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
    if user_data['is_admin']:
        await state.set_state(UserState.ADMIN)
        await message.answer(
            text=f'Привет {user_data['name']}',
            reply_markup=admin_menu()
        )
        return

    await state.set_state(UserState.WAITING_FOR_ANSWERS)
    question_id = 'qst_1'
    question = messages.QUESTIONS[question_id]
    await message.answer(
        text=f'Привет {user_data['name']}',
        reply_markup=types.ReplyKeyboardRemove()
    )
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
    prefix, question_number, answer_value = callback.data.split('_')
    question_number = int(question_number)
    question_id = f'{prefix}_{question_number}'

    await callback.message.edit_reply_markup(reply_markup=None)

    # Получаем вопрос из словаря
    question = messages.QUESTIONS.get(question_id)
    if not question:
        await callback.message.answer('Ошибка: вопрос не найден.')
        return

    # Сохраняем ответ в state
    await process_answer(state, answer_value, question_id)

    if question_id == 'qst_1' and answer_value == 'False':
        await callback.message.answer(
            'Очень жаль, что ты не сможешь прийти. 😢'
        )
        await state.set_state(UserState.FRAUD)
        return

    # Отправляем следующий вопрос (если есть)
    next_question_id = f'{prefix}_{question_number + 1}'
    if next_question_id in messages.QUESTIONS:
        next_question = messages.QUESTIONS[next_question_id]
        await callback.message.answer(
            text=next_question['text'],
            reply_markup=create_qst_inline_kb(next_question_id, next_question),
        )
    else:
        user_data = await state.get_data()
        await save_answers_to_redis(user_data)

        await state.set_state(UserState.REGISTERED)
        await callback.message.answer(
            messages.END_POLL_MESSAGE, reply_markup=make_menu()
        )


@router.message(StateFilter(UserState.REGISTERED), F.text.contains('НАЖМИ'))
async def info(message: types.Message, state: FSMContext):
    await message.answer(messages.FLOWERS_INFO_MESSAGE)


@router.message(StateFilter(UserState.REGISTERED),
                F.text.contains('Расписание'))
async def schedule(message: types.Message, state: FSMContext):
    await message.answer(messages.SСHEDULLE_MESSAGE)


@router.message(StateFilter(UserState.REGISTERED),
                F.text.contains('Место проведения'))
async def geo(message: types.Message, state: FSMContext):
    latitude = 55.157992
    longitude = 61.152166

    await message.answer_location(
        latitude=latitude,
        longitude=longitude,
    )

    await message.answer(messages.GEO_MESSAGE)


@router.message(StateFilter(UserState.REGISTERED),
                F.text.contains('Пройти опрос заново'))
async def restart_poll(message: types.Message, state: FSMContext):
    await  state.set_state(UserState.WAITING_FOR_ANSWERS)

    question_id = 'qst_1'
    question = messages.QUESTIONS[question_id]

    user_data = await state.get_data()
    await message.answer(
        text=f'{user_data['name']}, Опрос перезапущен!',
        reply_markup=types.ReplyKeyboardRemove()
    )

    await asyncio.sleep(1)
    await message.answer(
        text=question['text'],
        reply_markup=create_qst_inline_kb(question_id, question),
    )


def format_user_key(key):
    return key.replace('user:', '')


async def get_all_users():
    user_keys = await redis_client.keys('user:*')
    return user_keys


async def get_user_data(user_key):
    return await redis_client.hgetall(user_key)


async def get_users_by_answer(question_id, answer_value):
    user_keys = await get_all_users()
    users = []

    for key in user_keys:
        answer = await redis_client.hget(key, question_id)
        if answer == answer_value:
            users.append(format_user_key(key))

    return users


async def get_non_responding_users():
    db_users = {user_info['name'] for user_info in settings.DB.values()}
    redis_users = {format_user_key(key) for key in await get_all_users()}
    return db_users - redis_users


def format_poll_results(user_data):
    formatted_results = []
    for key, value in user_data.items():
        if key in messages.QUESTIONS:
            question_data = messages.QUESTIONS[key]
            question_text = question_data['admin_text']
            answer_text = question_data['answers'].get(value, 'неизвестно')
            formatted_results.append(f'{question_text} - {answer_text}')
    return '; '.join(formatted_results)


@router.message(F.text == 'Результаты опроса', StateFilter(UserState.ADMIN))
async def poll_results(message: types.Message):
    user_keys = await get_all_users()
    results = []

    for key in user_keys:
        user_data = await get_user_data(key)
        name = key.replace('user:', '')
        formatted_results = format_poll_results(user_data)
        results.append(f'{name}: {formatted_results}')

    if results:
        await message.answer('Результаты опроса:\n' + '\n'.join(results))
    else:
        await message.answer('Нет данных о результатах опроса.')


@router.message(F.text == 'Кто придет?', StateFilter(UserState.ADMIN))
async def who_come(message: types.Message):
    coming_users = await get_users_by_answer('qst_1', 'True')

    if coming_users:
        await message.answer('Придут на свадьбу:\n' + '\n'.join(coming_users))
    else:
        await message.answer('Нет данных о тех, кто придет.')


@router.message(F.text == 'Кто не придет?', StateFilter(UserState.ADMIN))
async def who_fraud(message: types.Message):
    fraud_users = await get_users_by_answer(1, 'False')

    if fraud_users:
        await message.answer(
            'Не придут на свадьбу:\n' + '\n'.join(fraud_users))
    else:
        await message.answer('Нет данных о тех, кто не придет.')


@router.message(F.text == 'Остальные', StateFilter(UserState.ADMIN))
async def others(message: types.Message):
    others_users = await get_non_responding_users()

    if others_users:
        await message.answer(
            'Пользователи, не ответившие на опрос:\n' + '\n'.join(
                others_users))
    else:
        await message.answer('Нет пользователей, не ответивших на опрос.')


@router.message(Command('reset'))
async def reset(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Состояние сброшено', reply_markup=start_menu())


@router.message(F.text)
async def unknown_command(message: types.Message, state: FSMContext):
    logging.error(f'unknown user state: {state}')

    if state == UserState.FRAUD:
        await message.answer('Очень жаль, что ты не сможешь прийти. 😢')
        return

    if state is not None:
        reply_markup = types.ReplyKeyboardRemove()
        if state == UserState.REGISTERED:
            reply_markup = make_menu()

        await message.answer(
            'Доступны только команды из меню', reply_markup=reply_markup
        )
        return

    await message.answer('Мы не знакомы', reply_markup=start_menu())
