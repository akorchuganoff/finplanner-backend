import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models import Category, CategoryType 

def seed_system_categories():
    db = SessionLocal()
    try:
        # Список системных категорий
        system_categories = [
            # Доходы
            ("Зарплата", CategoryType.income),
            ("Фриланс", CategoryType.income),
            ("Инвестиционный доход", CategoryType.income),
            ("Подарки", CategoryType.income),
            ("Прочее", CategoryType.income),
            # Расходы
            ("Продукты", CategoryType.expense),
            ("Транспорт", CategoryType.expense),
            ("Рестораны", CategoryType.expense),
            ("Развлечения", CategoryType.expense),
            ("Одежда", CategoryType.expense),
            ("Здоровье", CategoryType.expense),
            ("Образование", CategoryType.expense),
            ("Коммунальные платежи", CategoryType.expense),
            ("Связь", CategoryType.expense),
            ("Прочее", CategoryType.expense),
        ]

        # Проверяем, есть ли уже какие-либо системные категории
        existing = db.query(Category).filter(Category.user_id.is_(None)).first()
        if existing:
            print("System categories already exist. Skipping seed.")
            return

        for name, cat_type in system_categories:
            category = Category(name=name, type=cat_type, user_id=None)
            db.add(category)

        db.commit()
        print(f"Seeded {len(system_categories)} system categories.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_system_categories()