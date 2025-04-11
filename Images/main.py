import asyncio
import os
from Const import *

from aiogram import Bot, Dispatcher, F
from aiogram.types.input_media_document import InputMediaDocument
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from Middlewares.AlbumWare import AlbumMiddleware
AbsolutePath = os.path.dirname(__file__)
imgpath = (AbsolutePath + r'\\Images\\')
btlpath = (AbsolutePath + r'\\Battle\\')
dp = Dispatcher()
dp.message.middleware(AlbumMiddleware(latency=0.1))
#States
class UserState(StatesGroup):
    registred = State()
    RecivingImages = State()
#Command handler
async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

@dp.message(F.text.contains(hashtag1), StateFilter(UserState.registred)) 
async def BulkBattleSend(message: Message, state: FSMContext):
    await state.set_state(UserState.RecivingImages)
    await message.reply('Следущая группа файлов (2+ сжатые фотографии) будет сохранена и переслана в чат с хэштэгом #баттл.')
@dp.message(F.media_group_id, StateFilter(UserState.RecivingImages))
async def BulkBattleAccept(message: Message, state: FSMContext, album: list = None):
    g = 0
    media_group = []
    if album:
        for i in range(int(len(album) // 2)): #название и айди файла идут парами, тоесть на каждое фото идет 2 элемента списка
            await message.bot.download(file=album[g], destination=(btlpath + (str(message.from_user.id) + '_' + album[g+1])))
            media_group.append(InputMediaDocument(media=album[g]))
            g = g + 2
        await message.bot.send_message(message_thread_id=BattleTopic_id, chat_id=chat_id, text=f'Альбом из {len(album) // 2} фотографий от @{message.from_user.username}')
        await message.bot.send_media_group(chat_id=chat_id, message_thread_id=BattleTopic_id, media=media_group)
        await message.reply(f'Принято и переслано {len(album) // 2} фотографий. ')
        await state.set_state(UserState.registred)
    else:
        await message.reply('Ошибка')
        await state.set_state(UserState.registred)
@dp.message(F.media_group_id, StateFilter(UserState.registred))
async def GroupMediaGet(message: Message, album: list = None): #обработка альбомов через Middleware "AlbumWare"
    g = 0
    if album:
        for i in range(int(len(album) // 2)): #название и айди файла идут парами, тоесть на каждое фото идет 2 элемента списка
            await message.bot.download(file=album[g], destination=(imgpath + album[g+1]))
            g = g + 2
        await message.reply(f'Принято {len(album) // 2} фотографий.')
    else:
        await message.reply('Ошибка')
@dp.message(Command("anonimg"), StateFilter(UserState.registred)) #команда для отправки всех изображений разом, планирую сделать фильтр по пользователям
async def BulkImageSending(message: Message) -> None:
    await message.bot.send_message(message_thread_id=ImageTopic_id, chat_id=chat_id, text="фотографии 14 илюня вечерером")
    absImage = [os.path.abspath(os.path.join(directory, p)) 
                for p in os.listdir(directory) 
                if p.endswith(('jpg', 'png'))] #выбор всех файлов с расширениями, представленными ниже
    for i in range(len(absImage)):
        await message.bot.send_document(message_thread_id=ImageTopic_id, chat_id=chat_id, document=FSInputFile(absImage[i]), 
                                        caption=None)#(os.path.basename(absImage[i].split('.')[0]))) #подпись будет названием картинки
        #пауза для анти-флуд системы телеграма. Максимум 20 картинок в минуту(3 картинки в секунду)
        await asyncio.sleep(3)
@dp.message(F.document, StateFilter(UserState.registred))
async def get_photo(message: Message):
    #проверка есть ли подпись к файлу
    msgcaption = message.caption
    if msgcaption is None: msgcaption = ['Нет подписи']
    else: msgcaption = msgcaption.split(' ')
    if any(f'{hashtag1}' in i for i in msgcaption) == True: #переслать файл если есть тэг баттл(hashtag1) в подписе
        await message.bot.download(file=message.document.file_id, destination=(btlpath + (str(message.from_user.id) +  '_' + message.document.file_name)))
        await message.bot.send_document(message_thread_id=BattleTopic_id, chat_id=chat_id, document=message.document.file_id, caption=f'Фотография от @{message.from_user.username}')
        await message.reply(f'Фотография с тэгом {hashtag1} была сохранена и переслана в отдельный чат.')
    else:
        await message.bot.download(file=message.document.file_id, destination=(imgpath + (str(message.from_user.id) + '_' + message.document.file_name)))
        await message.reply('Принята 1 фотография.')    
#run bot
if __name__ == "__main__":
    asyncio.run(main())