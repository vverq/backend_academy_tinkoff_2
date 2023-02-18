import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

USERS = dict()
FRIENDS = dict()


class User(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1, max_length=140)
    age: int = Field(gt=0)
    email: EmailStr


class Friends(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    id_friend_one: UUID
    id_friend_two: UUID


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()


@app.post("/users/", tags=["user"], description="Create new user")
async def create_user(user: User):
    USERS[user.id] = user
    return user.id


@app.put("/users/{user_id}", tags=["user"], description="Update user, who already exists")
async def update_user(user_id: UUID, user: User):
    if user_id in USERS.keys():
        USERS[user_id] = user
        return user


@app.get("/users/{user_id}", tags=["user"], description="Get user by id")
async def get_user(user_id: UUID):
    if user_id in USERS.keys():
        return USERS[user_id]
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/",  tags=["users"], description="Get all users")
async def get_users():
    return USERS


@app.post("/users/friends/", tags=["friendship"], description="Create friendship between user1 and user2 by their ids")
async def create_friends(friends: Friends):
    if friends.id_friend_one in USERS.keys():
        if friends.id_friend_two in USERS.keys():
            FRIENDS[friends.id] = friends
            return
        raise HTTPException(status_code=404, detail=f"User with id {friends.id_friend_two} not found")
    raise HTTPException(status_code=404, detail=f"User with id {friends.id_friend_one} not found")
