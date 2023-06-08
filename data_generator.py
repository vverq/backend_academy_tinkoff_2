import random
import uuid
import datetime
import asyncio
import asyncpg
from faker import Faker

fake = Faker()

COUNT = 2_000_000


async def run():
    conn = await asyncpg.connect(
        host='0.0.0.0',
        port=5432,
        database='postgres',
        user='admin',
        password='pwd'
    )
    template_users = '''
        INSERT INTO users (id, name, description, age, email, password, login_date)
        VALUES {};
        '''
    template_friendship = '''
        INSERT INTO friendship (id, friend_id_one, friend_id_two)
        VALUES {};
        '''

    template_users_values = '''('{}', '{}', '{}', {}, '{}', '{}', '{}')'''
    template_friendship_values = '''('{}', '{}', '{}')'''

    print("start")

    uuids = [uuid.uuid4() for _ in range(COUNT)]

    data_users = [template_users_values.format(
        uuids[i],
        fake.first_name(),
        fake.sentence(),
        random.randint(18, 100),
        fake.email(),
        fake.password(),
        datetime.datetime.utcnow()
    ) for i in range(COUNT)]

    print("data users prepared")

    data_friendship = [template_friendship_values.format(
        uuid.uuid4(),
        uuids[i],
        uuids[i + 1]
    ) for i in range(COUNT - 1)]

    data_friendship_first = [template_friendship_values.format(
        uuid.uuid4(),
        uuids[i],
        uuids[i + 2]
    ) for i in range(COUNT - 2)]

    data_friendship_second = [template_friendship_values.format(
        uuid.uuid4(),
        uuids[i],
        uuids[i - 1]
    ) for i in range(1, COUNT)]

    print("data ready")
    await conn.fetch(template_users.format(','.join(data_users)))
    await conn.fetch(template_friendship.format(','.join(data_friendship)))
    await conn.fetch(template_friendship.format(','.join(data_friendship_first)))
    await conn.fetch(template_friendship.format(','.join(data_friendship_second)))

    print("insert ready")
    await conn.commit()
    await conn.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
