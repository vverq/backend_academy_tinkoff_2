from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Index
from sqlalchemy import UUID

from .database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True,  index=True)
    name = Column(String)
    description = Column(String)
    age = Column(Integer)
    email = Column(String)
    password = Column(String)
    login_date = Column(DateTime, default=None)


class Friendship(Base):
    __tablename__ = 'friendship'
    friend_id_one = Column(UUID, ForeignKey('users.id'), index=True, primary_key=True)
    friend_id_two = Column(UUID, ForeignKey('users.id'),  index=True, primary_key=True)
