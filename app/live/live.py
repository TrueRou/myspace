import datetime

from fastapi import APIRouter, Depends, Form
from sqlalchemy import select
from datetime import datetime

from starlette.requests import Request

from app.databases import Live, User, Message, async_session_maker, LiveLinks
from app.schemas import LiveCreation
from app.users import current_active_user, current_active_user_optional
from cache import append_message_cache, append_online_users, get_online_users, \
    get_messages, append_not_logged_users, not_logged_users

live_router = APIRouter(prefix='/live', tags=["live"])


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
async def create_live(params: LiveCreation, user: User = Depends(current_active_user)):
    if user.live_available:
        async with async_session_maker() as session:
            async with session.begin():
                session.add(
                    Live(title=params.title, beginning_time=datetime.now(), description=params.description, owner=user.username, link=params.link))
        return {'status': 'success'}
    else:
        return {'status': 'failure', 'message': 'No permission'}


@live_router.get("/link")
async def get_live_link():
    async with async_session_maker() as session:
        live = await session.scalar(select(Live).order_by(Live.beginning_time.desc()))
        if live is None:
            return {
                'status': 'error',
                'msg': 'There is no live existed.'
            }
        return {
            'status': 'success',
            'link': live.link
        }


@live_router.get("/links")
async def get_live_links(user: User = Depends(current_active_user)):
    if user.live_available:
        async with async_session_maker() as session:
            entries = await session.scalars(select(LiveLinks))
            items = []
            for item in entries:
                items.append(item)
            return {
                'status': 'success',
                'links': items
            }
    else:
        return {'status': 'failure', 'message': 'No permission'}


@live_router.post("/links")
async def create_live_links(label: str, link: str, user: User = Depends(current_active_user)):
    if user.live_available:
        async with async_session_maker() as session:
            async with session.begin():
                session.add(
                    LiveLinks(link=link, label=label))
        return {'status': 'success'}
    else:
        return {'status': 'failure', 'message': 'No permission'}


@live_router.delete("/links")
async def remove_live_links(id: int, user: User = Depends(current_active_user)):
    if user.live_available:
        async with async_session_maker() as session:
            async with session.begin():
                link = (await session.scalar(select(LiveLinks).where(LiveLinks.id == id)))
                await session.delete(link)
        return {'status': 'success'}
    else:
        return {'status': 'failure', 'message': 'No permission'}
