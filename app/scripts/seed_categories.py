import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models import Category

def seed_system_categories():
    db = SessionLocal()
    try:
        # Список системных категорий
        system_categories = [
            # Доходы
            ("Зарплата", "income"),
            ("Фриланс", "income"),
            ("Инвестиционный доход", "income"),
            ("Подарки", "income"),
            ("Прочее", "income"),
            # Расходы
            ("Продукты", "expense"),
            ("Транспорт", "expense"),
            ("Рестораны", "expense"),
            ("Развлечения", "expense"),
            ("Одежда", "expense"),
            ("Здоровье", "expense"),
            ("Образование", "expense"),
            ("Коммунальные платежи", "expense"),
            ("Связь", "expense"),
            ("Прочее", "expense"),
        ]

        # Проверяем, есть ли уже какие-либо системные категории
        existing = db.query(Category).filter(Category.user_id.is_(None)).first()
        if existing:
            print("System categories already exist. Skipping seed.")
            return

        for name, cat_type in system_categories:
            category = Category(name=name, category_type=cat_type, user_id=None)
            db.add(category)

        db.commit()
        print(f"Seeded {len(system_categories)} system categories.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_system_categories()