from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import UUID

from .database import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(UUID, primary_key=True)
    name = Column(String)
    description = Column(String)
    age = Column(Integer)
    email = Column(String)
    password = Column(String)


class Friendship(Base):
    __tablename__ = 'author'
    id = Column(UUID, primary_key=True)
    friend_id_one = Column(UUID, ForeignKey('user.id'))
    friend_id_two = Column(UUID, ForeignKey('user.id'))