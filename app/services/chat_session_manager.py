from collections import defaultdict
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio

class ChatSessionManager:
    """
    Управляет сессиями чата. Хранит историю сообщений в памяти.
    Для production стоит заменить на Redis.
    """
    def __init__(self, ttl_seconds: int = 3600):  # время жизни сессии 1 час
        self.sessions: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self.last_activity: Dict[str, datetime] = {}
        self.ttl = ttl_seconds
        self._cleanup_task = None

    def start_cleanup(self):
        """Запускает фоновую очистку устаревших сессий."""
        async def cleanup():
            while True:
                await asyncio.sleep(300)  # каждые 5 минут
                now = datetime.now()
                expired = [sid for sid, last in self.last_activity.items() if now - last > timedelta(seconds=self.ttl)]
                for sid in expired:
                    del self.sessions[sid]
                    del self.last_activity[sid]
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(cleanup())

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Возвращает историю сообщений сессии."""
        self.last_activity[session_id] = datetime.now()
        return self.sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """Добавляет сообщение в историю."""
        self.sessions[session_id].append({"role": role, "content": content})
        self.last_activity[session_id] = datetime.now()
        # Ограничим длину истории (например, последними 20 сообщениями)
        if len(self.sessions[session_id]) > 20:
            self.sessions[session_id] = self.sessions[session_id][-20:]

    def clear_session(self, session_id: str):
        """Очищает историю сессии."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.last_activity:
            del self.last_activity[session_id]

# Глобальный экземпляр
session_manager = ChatSessionManager()
session_manager.start_cleanup()