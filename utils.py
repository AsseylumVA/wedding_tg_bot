from aiogram import Router, types
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import messages

router = Router()


class UserState(StatesGroup):
    NEW_USER = State()
    REGISTERED = State()
    FRAUD = State()
    WAITING_FOR_ANSWERS = State()


class AdminState(StatesGroup):
    ADMIN = State()
    SET_PHOTO = State()
    SENDING_MESSAGE = State()


async def edit_text(message: types.Message, question_id: str,
                    answer_value: str):
    new_text = f'{message.text} \n' \
               f'Ответ: {get_answer_text(question_id, answer_value)}'
    await message.edit_text(new_text)


async def process_answer(
        state: FSMContext,
        answer_value: str,
        question_id: str,
):
    # Сохраняем ответ в состоянии
    await state.update_data({f'{question_id}': answer_value})


def get_answer_text(question_id, value):
    question_data = messages.QUESTIONS[question_id]
    return question_data['answers'].get(value, 'неизвестно')


def format_user_key(key):
    return key.replace('user:', '')
