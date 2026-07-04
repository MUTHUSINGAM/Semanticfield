from fastapi import APIRouter, Depends

from models.schemas import ChatRequest, ChatResponse, UserRole
from services.auth import get_current_user, require_roles
from services.chat import process_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user=Depends(require_roles(UserRole.ADMIN, UserRole.SECURITY_OFFICER, UserRole.EMPLOYEE)),
):
    return await process_chat(user, body.message.strip())
