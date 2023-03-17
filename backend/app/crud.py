from uuid import UUID

from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_password(db: Session, email: str):
    return db.query(models.User.password).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


# todo можно без этой явной передачи полeй, а **user.dict()
def create_user(db: Session, user: schemas.User):
    db_item = models.User(id=user.id, name=user.name, description=user.description, age=user.age, email=user.email, password=user.password)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item.id


def update_user(db: Session, user_id: UUID, user: schemas.User):
    db.query(models.User).filter(models.User.id == user_id).update({
        "name": user.name, "description": user.description, "email": user.email, "age": user.age, "password": user.password
    })
    db.commit()
    return user


def create_friendship(db: Session, friends: schemas.Friends):
    db_item = models.Friendship(id=friends.id, friend_id_one=friends.id_friend_one, friend_id_two=friends.id_friend_two)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def find_friendship(db: Session, friend_id: UUID, user_id: UUID):
    return db.query(models.Friendship).filter((
            (models.Friendship.friend_id_one == friend_id) & (models.Friendship.friend_id_two == user_id)) |
            (models.Friendship.friend_id_one == user_id) & (models.Friendship.friend_id_two == friend_id)).first()
