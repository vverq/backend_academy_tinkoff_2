import datetime
import uuid
from pydantic import BaseModel, Field, EmailStr
from pydantic.types import Optional


class User(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1, max_length=140)
    age: int = Field(gt=0)
    email: EmailStr
    password: str
    login_date: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class Friends(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.id = None

    id_friend_one: uuid.UUID
    id_friend_two: uuid.UUID

    class Config:
        orm_mode = True
