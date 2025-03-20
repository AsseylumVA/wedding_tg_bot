from aiogram.methods import SendMessage

from .redis_mgr import RedisManager


class MessageSenderManger:
    def __init__(self):
        self.redis_manager = RedisManager()

    async def send_messages(self, message_text):
        user_keys = self.redis_manager.get_all_users()
        for user_key in user_keys:
            user_id = user_key.replace('user:')
            await SendMessage(chat_id=user_id, text = message_text)
