import datetime
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas


async def get_user(db: AsyncSession, user_id: UUID):
    return await db.execute(select(models.User).where(models.User.id == user_id))


async def get_user_by_email(db: AsyncSession, email: str):
    return await db.execute(select(models.User).where(models.User.email == email))


async def get_user_password(db: AsyncSession, email: str):
    return await db.execute(select(models.User.password).where(models.User.email == email))


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    return await db.execute(select(models.User).limit(limit))


async def create_user(db: AsyncSession, user: schemas.User):
    db_item = models.User(id=user.id, name=user.name, description=user.description, age=user.age, email=user.email,
                          password=user.password)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item.id


async def update_user(db: AsyncSession, user_id: UUID, user: schemas.User):
    await db.execute(update(models.User).where(models.User.id == user_id).values({
        "name": user.name, "description": user.description, "email": user.email, "age": user.age,
        "password": user.password
    }))
    await db.commit()
    return user


async def create_friendship(db: AsyncSession, friends: schemas.Friends):
    db_item = models.Friendship(friend_id_one=friends.id_friend_one, friend_id_two=friends.id_friend_two)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def find_friendship(db: AsyncSession, friend_id: UUID, user_id: UUID):
    return await db.execute(select(models.Friendship).where((
                                                                    (models.Friendship.friend_id_one == friend_id) & (
                                                                        models.Friendship.friend_id_two == user_id)) |
                                                            (models.Friendship.friend_id_one == user_id) & (
                                                                        models.Friendship.friend_id_two == friend_id)))


async def update_login_date(db: AsyncSession, user_id: UUID):
    await db.execute(update(models.User).where(models.User.id == user_id).values({
        "login_date": datetime.datetime.utcnow()
    }))
    await db.commit()


async def get_friends(db: AsyncSession, user_id: UUID):
    return await db.execute(select(models.User).filter(
        (models.Friendship.friend_id_one == user_id) | (models.Friendship.friend_id_two == user_id)
    ).where(models.User.id != user_id).order_by(models.User.id))
