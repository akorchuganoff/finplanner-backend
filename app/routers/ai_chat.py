from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.llm_service import llm_service
from app.services.chat_session_manager import session_manager
from app.services.analytics import get_multi_period_analytics
from app.prompts.financial_advisor import SYSTEM_PROMPT

router = APIRouter(prefix="/api/ai", tags=["ai"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # если не передан, создадим новый
    temperature: float = 0.7

class ChatResponse(BaseModel):
    response: str
    session_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Генерируем session_id, если не передан
    session_id = request.session_id
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    # Получаем историю сессии
    history = session_manager.get_history(session_id)
    
    # Формируем список сообщений для модели:
    # системный промпт + история + новое сообщение пользователя
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    messages.append({"role": "user", "content": request.message})
    
    try:
        # Вызываем LLM (не стриминг, для простоты)
        # llm_service.get_response ожидает user_message и system_prompt,
        # но для учета истории нужно модифицировать сервис.
        # Временно передаем всё одним сообщением, но лучше расширить сервис.
        # Сделаем временную функцию в llm_service, которая принимает список messages.
        response_text = await llm_service.get_response_with_messages(messages, temperature=request.temperature)
        
        # Сохраняем сообщения в историю
        session_manager.add_message(session_id, "user", request.message)
        session_manager.add_message(session_id, "assistant", response_text)
        
        return ChatResponse(response=response_text, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обращении к LLM: {str(e)}")