from fastapi import FastAPI
from app.database.database import engine, Base
from app.models import user  # чтобы загрузить модели

app = FastAPI(title="FinPlanner API")

@app.get("/")
def read_root():
    return {"message": "FinPlanner API is running"}