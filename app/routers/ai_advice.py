from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.analytics import get_multi_period_analytics
from app.services.llm_service import llm_service
from app.prompts.advice_template import build_advice_prompt
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/ai", tags=["ai"])

class AdviceResponse(BaseModel):
    advice: str
    periods_used: list[str] = ["short", "medium", "long"]

@router.post("/advice", response_model=AdviceResponse)
async def get_financial_advice(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. Получаем агрегированные данные по транзакциям пользователя
        analytics = get_multi_period_analytics(db, current_user.id)

        # 2. Формируем промпт на основе аналитики
        prompt = build_advice_prompt(analytics)

        # 3. Отправляем запрос к LLM (без системного промпта, всё включено в user message)
        advice = await llm_service.get_response(
            user_message=prompt,
            system_prompt=None,  # не нужен, т.к. промпт уже содержит инструкцию
            temperature=0.7,
            max_tokens=2000,
        )
        return AdviceResponse(advice=advice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении совета: {str(e)}")