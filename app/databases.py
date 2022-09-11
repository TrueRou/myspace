from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy import GUID
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./myspace.sqlite"
Base = declarative_base()


class User(SQLAlchemyBaseUserTableUUID, Base):
    username = Column(String(64))
    pass


class Live(Base):
    __tablename__ = "lives"

    id = Column(Integer, primary_key=True)
    title = Column(String(64))
    beginning_time = Column(DateTime())
    description = Column(String(128))
    owner = Column(String(64))


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    owner = Column(GUID)
    message = Column(String(512))
    datetime = Column(DateTime())


class TransferMessage(Base):
    __tablename__ = "transfer_messages"

    id = Column(Integer, primary_key=True)
    owner = Column(GUID)
    number = Column(String(64))
    body = Column(String(1024))
    received = Column(DateTime())
    remote_id = Column(Integer)


engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
