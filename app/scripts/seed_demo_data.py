#!/usr/bin/env python3
"""
Скрипт для создания демо-пользователя и тестовых данных для дашборда.
Запуск: python seed_demo_data.py
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# Добавляем путь к приложению для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal, engine
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.auth.auth import get_password_hash

# Загружаем переменные окружения
load_dotenv()

DEMO_EMAIL = "dashboard-demo-2-user@example.com"
DEMO_PASSWORD = "dashboard-demo-2-pass"

# Категории для демо-пользователя
INCOME_CATEGORIES = [
    "Зарплата", "Фриланс", "Инвестиции", "Подарки", "Проценты по вкладам"
]

EXPENSE_CATEGORIES = [
    "Продукты", "Транспорт", "Рестораны", "Развлечения", "Коммунальные платежи"
]

def create_demo_user(db):
    """Создаёт демо-пользователя, если его нет."""
    user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if user:
        print(f"Пользователь {DEMO_EMAIL} уже существует. Пропускаем.")
        return user
    hashed = get_password_hash(DEMO_PASSWORD)
    user = User(
        email=DEMO_EMAIL,
        hashed_password=hashed,
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Создан пользователь {DEMO_EMAIL} (id={user.id})")
    return user

def create_categories(db, user_id):
    """Создаёт категории для пользователя, если их ещё нет."""
    existing_cats = db.query(Category).filter(
        Category.user_id == user_id
    ).all()
    existing_names = {(c.name, c.category_type) for c in existing_cats}

    created = 0
    for name in INCOME_CATEGORIES:
        if (name, "income") not in existing_names:
            cat = Category(
                name=name,
                category_type="income",
                user_id=user_id
            )
            db.add(cat)
            created += 1
    for name in EXPENSE_CATEGORIES:
        if (name, "expense") not in existing_names:
            cat = Category(
                name=name,
                category_type="expense",
                user_id=user_id
            )
            db.add(cat)
            created += 1

    db.commit()
    print(f"Создано категорий: {created}")

def get_categories_dict(db, user_id):
    """Возвращает словарь {название: объект Category} для доходов и расходов."""
    cats = db.query(Category).filter(Category.user_id == user_id).all()
    income_cats = {c.name: c for c in cats if c.category_type == "income"}
    expense_cats = {c.name: c for c in cats if c.category_type == "expense"}
    return income_cats, expense_cats

def random_date(start_date, end_date):
    """Случайная дата между start_date и end_date."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def create_transactions(db, user_id, income_cats, expense_cats, count=100):
    """
    Создаёт count доходных и count расходных транзакций.
    Использует реалистичные распределения сумм и дат.
    """
    # Определяем диапазон дат: последние 3 месяца
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=730)

    existing_count = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    if existing_count >= 2 * count:
        print(f"У пользователя уже есть {existing_count} транзакций. Пропускаем создание.")
        return

    transactions_to_add = []

    # Доходы
    for _ in range(count):
        # Случайная категория из доходных
        cat = random.choice(list(income_cats.values()))
        # Сумма: от 1000 до 100000 (рублей), с шагом 0.01
        amount = Decimal(random.uniform(1000, 100000)).quantize(Decimal('0.01'))
        date = random_date(start_date, end_date)
        comment = random.choice(["Оплата по договору", "Перевод", "Бонус", "Возврат", ""])
        transactions_to_add.append(Transaction(
            amount=amount,
            transaction_type="income",
            date=date,
            comment=comment if comment else None,
            user_id=user_id,
            category_id=cat.id
        ))

    # Расходы
    for _ in range(count):
        cat = random.choice(list(expense_cats.values()))
        # Сумма: от 50 до 50000
        amount = Decimal(random.uniform(1000, 100000)).quantize(Decimal('0.01'))
        date = random_date(start_date, end_date)
        comment = random.choice(["Оплата картой", "Наличные", "Покупка", "Кафе", ""])
        transactions_to_add.append(Transaction(
            amount=amount,
            transaction_type="expense",
            date=date,
            comment=comment if comment else None,
            user_id=user_id,
            category_id=cat.id
        ))

    # Добавляем пакетно для производительности
    db.bulk_save_objects(transactions_to_add)
    db.commit()
    print(f"Создано транзакций: {2 * count} ({count} доходов, {count} расходов)")

def main():
    db = SessionLocal()
    try:
        print("Начинаем создание демо-данных...")
        user = create_demo_user(db)
        create_categories(db, user.id)
        income_cats, expense_cats = get_categories_dict(db, user.id)
        create_transactions(db, user.id, income_cats, expense_cats, count=1000)
        print("Готово!")
    except Exception as e:
        print(f"Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()