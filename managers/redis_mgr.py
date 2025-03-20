from redis.asyncio import Redis

import settings


class RedisManager:
    def __init__(self):
        self.redis_client = Redis(host='localhost', port=6379, db=0,
                                  decode_responses=True)

    async def save_answers_to_redis(self, user_data: dict):
        # Сохраняем все ответы в Redis
        user_id = user_data.pop('user_id')
        for key, value in user_data.items():
            await self.redis_client.hset(f'user:{user_id}', key, value)

    async def get_all_users(self):
        user_keys = await self.redis_client.keys('user:*')
        return user_keys

    async def get_user_data(self, user_key):
        return await self.redis_client.hgetall(user_key)

    async def get_users_by_answer(self, question_id, answer_value):
        user_keys = await self.get_all_users()
        users = []

        for key in user_keys:
            answer = await self.redis_client.hget(key, question_id)
            name = await self.redis_client.hget(key, 'name')
            if answer == answer_value:
                users.append(name)

        return users

    async def get_non_responding_users(self):
        db_users = {user_info['name'] for user_info in settings.DB.values()}
        user_keys = await self.get_all_users()
        redis_users = set()
        for key in user_keys:
            name = await self.redis_client.hget(key, 'name')
            redis_users.add(name)
        return db_users - redis_users

    async def set_settings(self, key, value):
        await self.redis_client.hset('settings', key, value)

    async def get_settings(self, key):
        return await self.redis_client.hget('settings', key)
