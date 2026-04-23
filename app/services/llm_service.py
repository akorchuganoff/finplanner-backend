import os
from typing import AsyncGenerator, Optional, List, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL", "Qwen/Qwen3-Coder-Next")

        if not self.api_key or not self.base_url:
            raise ValueError("API_KEY и ASE_URL должны быть установлены в .env")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0,
        )

    async def get_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 500,
    ) -> str:
        """
        Асинхронный запрос к Qwen.
        Возвращает полный ответ модели.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            presence_penalty=0,
        )
        return response.choices[0].message.content

    async def get_response_stream(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.5,
    ) -> AsyncGenerator[str, None]:
        """
        Асинхронный стриминг ответа от Qwen.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def get_response_with_messages(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.5,
        max_tokens: int = 2500,
    ) -> str:
        """Принимает готовый список сообщений (system, user, assistant) и возвращает ответ."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            presence_penalty=0,
        )
        return response.choices[0].message.content

# Глобальный экземпляр (можно заменить на dependency injection)
llm_service = LLMService()