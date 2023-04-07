from fastapi import APIRouter, Depends

import secret
from app.databases import User
from app.users import current_active_user

chatgpt_router = APIRouter(prefix='/chatgpt', tags=["chatgpt"])


@chatgpt_router.get("/token")
async def get_chatgpt_token(user: User = Depends(current_active_user)):
    if user.chat_available:
        return {'status': 'success', 'token': secret.chatgpt_secret}
    return {'status': 'failure', 'message': 'No permission'}
