import logging
from logging.handlers import TimedRotatingFileHandler

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

import messages
import settings
from keyboards import make_menu, start_menu, admin_menu
from managers.redis_mgr import RedisManager
from utils import AdminState, get_answer_text, UserState

redis_manager = RedisManager()
router = Router()

log_format = '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[TimedRotatingFileHandler(settings.LOG_FILE, when='d')],
)


def format_poll_results(user_data):
    formatted_results = []
    for key, value in user_data.items():
        if key in messages.QUESTIONS:
            question_data = messages.QUESTIONS[key]
            question_text = question_data['admin_text']
            answer_text = get_answer_text(key, value)
            formatted_results.append(f'{question_text} - {answer_text}')
    return '; '.join(formatted_results)


@router.message(F.text == 'Результаты опроса', StateFilter(AdminState.ADMIN))
async def poll_results(message: types.Message):
    user_keys = await redis_manager.get_all_users()
    results = []

    for key in user_keys:
        user_data = await redis_manager.get_user_data(key)
        name = user_data['name']
        formatted_results = format_poll_results(user_data)
        results.append(f'{name}: {formatted_results}')

    if results:
        await message.answer('Результаты опроса:\n' + '\n'.join(results))
    else:
        await message.answer('Нет данных о результатах опроса.')


@router.message(F.text == 'Кто придет?', StateFilter(AdminState.ADMIN))
async def who_come(message: types.Message):
    coming_users = await redis_manager.get_users_by_answer('qst_1', 'True')

    if coming_users:
        await message.answer('Придут на свадьбу:\n' + '\n'.join(coming_users))
    else:
        await message.answer('Нет данных о тех, кто придет.')


@router.message(F.text == 'Кто не придет?', StateFilter(AdminState.ADMIN))
async def who_fraud(message: types.Message):
    fraud_users = await redis_manager.get_users_by_answer('qst_1', 'False')

    if fraud_users:
        await message.answer(
            'Не придут на свадьбу:\n' + '\n'.join(fraud_users))
    else:
        await message.answer('Нет данных о тех, кто не придет.')


@router.message(F.text == 'Остальные', StateFilter(AdminState.ADMIN))
async def others(message: types.Message):
    others_users = await redis_manager.get_non_responding_users()

    if others_users:
        await message.answer(
            'Пользователи, не ответившие на опрос:\n' + '\n'.join(
                others_users))
    else:
        await message.answer('Нет пользователей, не ответивших на опрос.')


@router.message(StateFilter(AdminState.ADMIN), Command('set_welcome_photo'))
async def set_welcome_photo(message: types.Message, state: FSMContext):
    await state.set_state(AdminState.SET_PHOTO)
    await message.answer('Отправь приветственное фото',
                         reply_markup=types.ReplyKeyboardRemove())


@router.message(StateFilter(AdminState.SET_PHOTO), F.photo)
async def process_welcome_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await redis_manager.set_settings('welcome_photo_id', file_id)
    await state.set_state(AdminState.ADMIN)
    await message.answer('Новое фото установлено', reply_markup=admin_menu())


@router.message(StateFilter(AdminState.ADMIN), Command("stats"))
async def stats(message: types.Message):
    user_keys = await redis_manager.get_all_users()
    stats = {
        qst_id: {answer_key: 0 for answer_key in qst_data["answers"]}
        for qst_id, qst_data in messages.QUESTIONS.items()
    }

    for key in user_keys:
        user_data = await redis_manager.get_user_data(key)
        for qst_id, qst_answer in user_data.items():
            if qst_id not in stats:
                continue
            stats[qst_id][qst_answer] += 1

    result = []
    for qst_id, qst_data in messages.QUESTIONS.items():
        result.append(f"{qst_data['admin_text']}:")
        for answer_key, answer_text in qst_data["answers"].items():
            count = stats[qst_id].get(answer_key, 0)
            result.append(f"  {answer_text}: {count} чел.")

    # Отправляем результат
    await message.answer("\n".join(result))


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
