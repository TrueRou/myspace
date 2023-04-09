import uuid

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    manage_available: bool
    live_available: bool
    message_available: bool
    chat_available: bool
    message_baidu_available: bool
    pass


class UserCreate(schemas.BaseUserCreate):
    username: str
    pass


class UserUpdate(schemas.BaseUserUpdate):
    username: str
    manage_available: bool
    live_available: bool
    message_available: bool
    chat_available: bool
    message_baidu_available: bool
    pass


class LiveCreation(BaseModel):
    title: str
    description: str
    link: str
