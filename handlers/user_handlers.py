import asyncio
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from aiogram import F, Router, types, Bot
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.types.input_media_document import InputMediaDocument

import messages
import settings
from keyboards.admin_kb import admin_menu
from keyboards.user_kb import (
    create_qst_inline_kb,
    make_menu,
    new_user_menu,
    restart_poll_fraud,
    start_menu,
)
from managers.message_sender import MessageSenderManager
from managers.redis_mgr import RedisManager
from utils import (
    AdminState,
    edit_text,
    process_answer,
    UserState,
)

redis_manager = RedisManager()
router = Router()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=settings.LOG_FORMAT,
    handlers=[TimedRotatingFileHandler(settings.LOG_FILE, when='d')],
)


def get_current_time():
    return datetime.now(settings.TZ)


async def reset_user_data_to_default(state: FSMContext):
    data = await state.get_data()
    default_keys = {'user_id', 'name', 'phone', 'is_admin', 'full_name'}
    data = {key: value for key, value in data.items() if key in default_keys}
    await state.set_data(data)


@router.message(StateFilter(None), CommandStart())
async def start_new_user(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer(
        'Мы еще не знакомы. Нажми кнопку "Давай познакомимся!"',
        reply_markup=new_user_menu(),
    )
    return


@router.message(F.contact)
async def register(message: types.Message, state: FSMContext, bot: Bot):
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
    user_data['user_id'] = message.from_user.id
    user_data['phone'] = phone_number
    await state.update_data(user_data)

    if user_data['is_admin'] == 'True':
        await state.set_state(AdminState.ADMIN)
        await message.answer(
            text=f'Привет {user_data['name']}',
            reply_markup=admin_menu()
        )
        return

    now = get_current_time()
    if settings.START_TIME <= now:
        await redis_manager.save_user_data_to_redis(user_data)
        await state.set_state(UserState.REGISTERED)
        sender = MessageSenderManager(bot=bot)
        await sender.send_welcome_messages(message.from_user.id)
        return

    await message.answer_photo(
        await redis_manager.get_settings('welcome_photo'),
        caption=f'👋Здравствуй {user_data['name']}',
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(UserState.WAITING_FOR_ANSWERS)
    question_id = 'qst_1'
    question = messages.QUESTIONS[question_id]
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
    await edit_text(callback.message, question_id, answer_value)

    # Получаем вопрос из словаря
    question = messages.QUESTIONS.get(question_id)
    if not question:
        await callback.message.answer('Ошибка: вопрос не найден.')
        return

    # Сохраняем ответ в state
    await process_answer(state, answer_value, question_id)

    if question_id == 'qst_1' and answer_value == 'False':
        await callback.message.answer(
            'Очень жаль, что ты не сможешь прийти. 😢',
            reply_markup=restart_poll_fraud()
        )
        user_data = await state.get_data()
        await redis_manager.save_user_data_to_redis(user_data)
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
        await redis_manager.save_user_data_to_redis(user_data)

        await state.set_state(UserState.REGISTERED)
        await callback.message.answer(
            messages.END_POLL_MESSAGE, reply_markup=make_menu()
        )


@router.message(StateFilter(UserState.REGISTERED), F.text.contains('НАЖМИ'))
async def info(message: types.Message):
    await message.answer_photo(
        await redis_manager.get_settings('dress_photo'),
    )
    await message.answer(messages.FLOWERS_INFO_MESSAGE)


@router.message(StateFilter(UserState.REGISTERED),
                F.text.contains('Расписание'))
async def schedule(message: types.Message):
    await message.answer(messages.SСHEDULLE_MESSAGE)


@router.message(StateFilter(UserState.REGISTERED),
                F.text.contains('Место проведения'))
async def geo(message: types.Message):
    latitude = 55.157992
    longitude = 61.152166

    await message.answer_location(
        latitude=latitude,
        longitude=longitude,
    )

    await message.answer(messages.GEO_MESSAGE)


@router.message(StateFilter(UserState.REGISTERED, UserState.FRAUD),
                F.text.contains('Пройти опрос заново'))
async def restart_poll(message: types.Message, state: FSMContext):
    await redis_manager.del_user_data(message.from_user.id)
    await reset_user_data_to_default(state)

    await state.set_state(UserState.WAITING_FOR_ANSWERS)

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

@router.message(F.text.contains(settings.HASHTAG1), StateFilter(UserState.REGISTERED)) 
async def BulkBattleSend(message: types.Message, state: FSMContext):
    await state.set_state(UserState.RECIVING_IMAGES)
    await message.reply('Следущая группа файлов (2+ сжатые фотографии) будет сохранена и переслана в чат с хэштэгом #баттл.')

@router.message(F.media_group_id, StateFilter(UserState.RecivingImages))
async def BulkBattleAccept(message: types.Message, state: FSMContext, album: list = None):
    g = 0
    media_group = []
    if album:
        for i in range(int(len(album) // 2)): #название и айди файла идут парами, тоесть на каждое фото идет 2 элемента списка
            await message.bot.download(file=album[g], destination=(settings.BTL_PATH + (str(message.from_user.id) + '_' + album[g+1])))
            media_group.append(InputMediaDocument(media=album[g]))
            g = g + 2
        await message.bot.send_message(message_thread_id=settings.BATTLETOPIC_ID, chat_id=settings.CHAT_ID, text=f'Альбом из {len(album) // 2} фотографий от @{message.from_user.username}')
        await message.bot.send_media_group(chat_id=settings.CHAT_ID, message_thread_id=settings.BATTLETOPIC_ID, media=media_group)
        await message.reply(f'Принято и переслано {len(album) // 2} фотографий. ')
        await state.set_state(UserState.REGISTERED)
    else:
        await message.reply('Ошибка')
        await state.set_state(UserState.REGISTERED)

@router.message(F.media_group_id, StateFilter(UserState.REGISTERED))
async def GroupMediaGet(message: types.Message, album: list = None): #обработка альбомов через Middleware "AlbumWare"
    g = 0
    if album:
        for i in range(int(len(album) // 2)): #название и айди файла идут парами, тоесть на каждое фото идет 2 элемента списка
            await message.bot.download(file=album[g], destination=(settings.IMG_PATH + album[g+1]))
            g = g + 2
        await message.reply(f'Принято {len(album) // 2} фотографий.')
    else:
        await message.reply('Ошибка')

@router.message(F.document, StateFilter(UserState.REGISTERED))
async def get_photo(message: types.Message):
    #проверка есть ли подпись к файлу
    msgcaption = message.caption
    if msgcaption is None: msgcaption = ['Нет подписи']
    else: msgcaption = msgcaption.split(' ')
    if any(f'{settings.HASHTAG1}' in i for i in msgcaption) == True: #переслать файл если есть тэг баттл(hashtag1) в подписе
        await message.bot.download(file=message.document.file_id, destination=(settings.BTL_PATH + (str(message.from_user.id) +  '_' + message.document.file_name)))
        await message.bot.send_document(message_thread_id=settings.BATTLETOPIC_ID, chat_id=settings.CHAT_ID, document=message.document.file_id, caption=f'Фотография от @{message.from_user.username}')
        await message.reply(f'Фотография с тэгом {settings.HASHTAG1} была сохранена и переслана в отдельный чат.')
    else:
        await message.bot.download(file=message.document.file_id, destination=(settings.IMG_PATH + (str(message.from_user.id) + '_' + message.document.file_name)))
        await message.reply('Принята 1 фотография.')

@router.message(Command('reset'))
async def reset(message: types.Message, state: FSMContext):
    await redis_manager.del_user_data(message.from_user.id)
    await state.clear()
    await message.answer('Состояние сброшено', reply_markup=start_menu())

