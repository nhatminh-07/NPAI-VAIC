"""
Router cho AI Assistant (chatbot của frontend - component ChatWidget).

Endpoint: POST /assistant/chat
Request body: { "message": str, "history": [{"role": "user"|"assistant", "content": str}, ...] }
Response body, HTTP 200: { "reply": str }  # văn bản thuần tiếng Việt

Xem chi tiết hợp đồng API tại frontend/src/lib/api.ts (hàm sendChatMessage).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.assistant_service import build_reply

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    history = [turn.model_dump() for turn in payload.history]
    reply = build_reply(db, payload.message, history)
    return ChatResponse(reply=reply)