from redis.asyncio import Redis

import settings


class RedisManager:
    def __init__(self):
        self.redis_client = Redis.from_url(
            settings.REDIS_USER_DATA_DB,
            decode_responses=True,
        )

    async def save_answers_to_redis(self, user_data: dict):
        # Сохраняем все ответы в Redis
        user_id = user_data.pop('user_id')
        for key, value in user_data.items():
            await self.redis_client.hset(f'user:{user_id}', key, value)

    async def del_user_data(self, user_id):
        await self.redis_client.delete(f'user:{user_id}')

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
            name = await self.redis_client.hget(key, 'full_name')
            if answer == answer_value:
                users.append(name)

        return users

    async def get_non_responding_users(self):
        db_users = {user_info['full_name'] for user_info in
                    settings.DB.values() if
                    user_info['is_admin'] == 'False'}
        user_keys = await self.get_all_users()
        redis_users = set()
        for key in user_keys:
            name = await self.redis_client.hget(key, 'full_name')
            redis_users.add(name)
        return db_users - redis_users

    async def set_settings(self, key, value):
        await self.redis_client.hset('settings', key, value)

    async def get_settings(self, key):
        return await self.redis_client.hget('settings', key)
