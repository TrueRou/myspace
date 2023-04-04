from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Form
from sqlalchemy import select, and_

from app.databases import User, TransferMessage, async_session_maker, ShareRules
from app.users import current_active_user
import time

transfer_router = APIRouter(prefix='/transfer')


@transfer_router.post("/entries")
async def add_entry(number: str, received: datetime, body: str, _id: int, owner: str):
    try:
        UUID(owner)
    except ValueError:
        return {'status': 'failed', 'msg': 'Illegal UUID Format'}
    async with async_session_maker() as session:
        async with session.begin():
            if await session.scalar(select(User).where(User.id == owner)) is None:
                return {'status': 'failed', 'msg': 'User not found'}
            statement = and_(TransferMessage.owner == owner, TransferMessage.remote_id == _id)
            if await session.scalar(select(TransferMessage).where(statement)) is not None:
                return {'status': 'skipped', 'msg': 'The entry is already exist'}
            session.add(TransferMessage(owner=owner, number=number, body=body, remote_id=_id, received=received))
    return {'status': 'success'}


@transfer_router.post("/webhook")
async def add_entry_webhook(token: str, payload: str = Form()):
    result = payload.split('\n')
    received = datetime.strptime(result[3], '%Y-%m-%d %H:%M:%S')
    return await add_entry(result[0], received, result[1], int(time.time()), token)


@transfer_router.get("/entries")
async def get_entry(user: User = Depends(current_active_user)):
    async with async_session_maker() as session:
        statement = select(TransferMessage) \
            .where(TransferMessage.owner == user.id) \
            .order_by(TransferMessage.received.desc()) \
            .limit(10)
        entries = await session.scalars(statement)
        items = []
        for item in entries:
            items.append(item)
    return {
        'status': 'success',
        'user': user,
        'entries': items
    }


async def get_entry_specific(keyword: str, session):
    statement = select(TransferMessage) \
        .where(TransferMessage.body.like(keyword)) \
        .order_by(TransferMessage.received.desc()) \
        .limit(10)
    return await session.scalars(statement)


@transfer_router.get("/entries/share")
async def get_shared_messages(user: User = Depends(current_active_user)):
    async with async_session_maker() as session:
        statement = select(ShareRules).where(and_(ShareRules.user_id == user.id, ShareRules.share_type == 0))
        items = []
        if await session.scalar(statement) is not None:
            for item in await get_entry_specific("百度账号", session):
                items.append(item)
    return {
        'status': 'success',
        'user': user,
        'entries': items
    }
