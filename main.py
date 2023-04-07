import datetime
import warnings
from typing import List

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends
from datetime import datetime, timedelta

from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

import secret
from app import schemas
from app.chatgpt.chatgpt import chatgpt_router
from app.databases import create_db_and_tables, User, async_session_maker
from app.live.live import live_router
from app.schemas import UserCreate, UserRead, UserUpdate
from app.transfer.transfer import transfer_router
from app.users import auth_backend, fastapi_users, current_active_user
from cache import online_users, not_logged_users

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)

app = FastAPI()
Schedule = AsyncIOScheduler()

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)


@app.get("/manage/users", response_model=List[schemas.UserRead])
async def get_all_users(user: User = Depends(current_active_user)):
    if user.is_superuser and user.manage_available:
        async with async_session_maker() as session:
            entries = await session.scalars(select(User))
            items = []
            for item in entries:
                items.append(item)
            return items


app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
)
app.include_router(live_router)
app.include_router(transfer_router)
app.include_router(chatgpt_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def main_page():
    return {"message": f"Welcome to our backend!"}


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    Schedule.start()
    Schedule.add_job(check_online, 'interval', seconds=30)


def check_online():
    for index, user in enumerate(online_users):
        last_active = user['last_activity']
        if last_active + timedelta(seconds=30) < datetime.now():
            online_users.pop(index)
    for index, user in enumerate(not_logged_users):
        last_active = user['last_activity']
        if last_active + timedelta(seconds=30) < datetime.now():
            not_logged_users.pop(index)


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=7001)
