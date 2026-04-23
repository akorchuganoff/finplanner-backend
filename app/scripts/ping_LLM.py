import asyncio
from app.services.llm_service import llm_service

async def main():
    response = await llm_service.get_response("Как я могу улучшить my finances?", system_prompt="Ты финансовый консультант.")
    print(response)

asyncio.run(main())