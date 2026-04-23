# app/services/analytics.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.models.transaction import Transaction
from app.models.category import Category

def get_aggregated_data(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Возвращает агрегированные данные по транзакциям пользователя за период.
    """
    # Общие суммы доходов и расходов
    totals = db.query(
        func.sum(Transaction.amount).filter(Transaction.transaction_type == 'income').label('total_income'),
        func.sum(Transaction.amount).filter(Transaction.transaction_type == 'expense').label('total_expense')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).first()
    
    total_income = totals.total_income or Decimal(0)
    total_expense = totals.total_expense or Decimal(0)
    balance = total_income - total_expense
    
    # Топ категорий расходов
    expense_by_category = (
        db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'expense',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )
    
    # Топ категорий доходов
    income_by_category = (
        db.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'income',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )
    
    # Количество транзакций
    transaction_count = db.query(func.count(Transaction.id)).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).scalar() or 0
    
    # Средний дневной расход (если есть транзакции)
    days = (end_date - start_date).days or 1
    avg_daily_expense = total_expense / days
    
    # Формируем результат
    return {
        "period": f"{start_date.isoformat()} - {end_date.isoformat()}",
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "balance": float(balance),
        "transaction_count": transaction_count,
        "avg_daily_expense": float(avg_daily_expense),
        "top_expense_categories": [{"name": cat, "amount": float(amount)} for cat, amount in expense_by_category],
        "top_income_categories": [{"name": cat, "amount": float(amount)} for cat, amount in income_by_category],
    }

def get_multi_period_analytics(
    db: Session,
    user_id: int,
    current_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Возвращает аналитику за три периода: краткосрочный, среднесрочный, долгосрочный.
    """
    if current_date is None:
        current_date = date.today()
    
    periods = {
        "short": (current_date - timedelta(days=14), current_date),   # 2 недели
        "medium": (current_date - timedelta(days=90), current_date),  # 3 месяца
        "long": (current_date - timedelta(days=365), current_date),   # 1 год
    }
    
    result = {}
    for period_name, (start, end) in periods.items():
        result[period_name] = get_aggregated_data(db, user_id, start, end)

    result['monthly_timeline'] = get_monthly_timeline(db, user_id, months_back=12)
    
    return result

def get_monthly_timeline(
    db: Session,
    user_id: int,
    months_back: int = 12
) -> List[Dict[str, Any]]:
    """
    Возвращает доходы, расходы и баланс по месяцам за последние N месяцев.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=months_back*30)
    
    results = db.query(
        func.date_trunc('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).filter(Transaction.transaction_type == 'income').label('income'),
        func.sum(Transaction.amount).filter(Transaction.transaction_type == 'expense').label('expense')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).group_by('month').order_by('month').all()
    
    timeline = []
    for month, inc, exp in results:
        timeline.append({
            "month": month.strftime("%Y-%m"),
            "income": float(inc) if inc else 0,
            "expense": float(exp) if exp else 0,
            "balance": float((inc or 0) - (exp or 0))
        })
    return timeline