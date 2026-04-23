import asyncio
from typing import AsyncGenerator, Optional

class StubLLMService:
    async def get_response(self, user_message: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        await asyncio.sleep(0.5)
        if "привет" in user_message.lower():
            return "Здравствуйте! Я финансовый помощник. Задайте вопрос о ваших транзакциях."
        if "совет" in user_message.lower():
            return "Тестовый совет: попробуйте сократить расходы на кафе на 20% в этом месяце."
        return f"Заглушка: вы написали: {user_message[:100]}..."

    async def get_response_stream(self, user_message: str, system_prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        test_response = "Это тестовый ответ от заглушки. "
        for word in test_response.split():
            yield word + " "
            await asyncio.sleep(0.1)