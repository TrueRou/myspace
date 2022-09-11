from datetime import datetime

from fastapi_users_db_sqlalchemy import GUID

from app.databases import User, async_session_maker

online_users = []
not_logged_users = []
cached_messages = []
cached_user_names = dict()


def append_message_cache(message: str, user: User):
    new_message = {
        'id': user.id,
        'message': message
    }
    if len(cached_messages) == 11:
        cached_messages.pop(0)
    cached_messages.append(new_message)


def append_online_users(user: User):
    append = True
    for item in online_users:
        if item['id'] == user.id:
            append = False
            break
    if append:
        online_users.append({
            'id': user.id,
            'last_activity': datetime.now()
        })


def append_not_logged_users(ip: str):
    append = True
    for item in not_logged_users:
        if item['ip'] == ip:
            append = False
            break
    if append:
        not_logged_users.append({
            'ip': ip,
            'last_activity': datetime.now()
        })


async def get_online_users():
    target = []
    for item in online_users:
        target.append({
            'username': await name_from_sql_or_cache(item['id'])
        })
    return target


async def get_messages():
    target = []
    for item in cached_messages:
        target.append({
            'username': await name_from_sql_or_cache(item['id']),
            'message': item['message']
        })
    return target


async def name_from_sql_or_cache(user_id: GUID) -> str:
    if user_id in cached_user_names.keys():
        return cached_user_names[user_id]
    else:
        async with async_session_maker() as session:
            username = (await session.get(User, user_id)).username
        return username
