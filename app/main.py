from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.routers import categories
from app.routers import transactions
from app.routers import import_data
from app.database.database import engine, Base
import app.models.user  # чтобы Alembic видел модель
import app.models.category  # чтобы Alembic видел модель
import app.models.transaction


app = FastAPI(title="FinPlanner API")

# Настройка CORS (разрешаем запросы с фронтенда)
origins = [
    "http://localhost:5173",  # Vite по умолчанию
    "http://localhost:3000",  # альтернативный порт
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # обязательно для передачи cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(import_data.router)

@app.get("/")
def read_root():
    return {"message": "FinPlanner API is running"}