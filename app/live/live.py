import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from datetime import datetime

from starlette.requests import Request

from app.databases import Live, User, Message, async_session_maker
from app.users import current_active_user, current_active_user_optional
from cache import append_message_cache, append_online_users, get_online_users, \
    get_messages, append_not_logged_users, not_logged_users

live_router = APIRouter(prefix='/live')


@live_router.get("/status")
async def live_status(request: Request, user: User = Depends(current_active_user_optional)):
    async with async_session_maker() as session:
        live = await session.scalar(select(Live).order_by(Live.beginning_time.desc()))
        if live is None:
            return {
                'status': 'error',
                'msg': 'There is no live existed.'
            }
    if user is not None:
        append_online_users(user)
    else:
        append_not_logged_users(request.client.host)
    return {
        'status': 'success',
        'online': user is not None,
        'title': live.title,
        'beginning_time': live.beginning_time,
        'description': live.description,
        'owner': live.owner,
        'online_users': await get_online_users(),
        'messages': await get_messages(),
        'not_logged_user_count': len(not_logged_users)
    }


@live_router.post("/message")
async def send_message(message: str, user: User = Depends(current_active_user)):
    append_message_cache(message, user)
    async with async_session_maker() as session:
        async with session.begin():
            session.add(Message(owner=user.id, message=message, datetime=datetime.now()))
    return {'status': 'success'}


@live_router.post("/create")
async def create_live(title: str, description: str, owner: str):
    async with async_session_maker() as session:
        async with session.begin():
            session.add(Live(title=title, beginning_time=datetime.now(), description=description, owner=owner))
    return {'status': 'success'}
