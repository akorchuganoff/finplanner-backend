from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case, extract
from decimal import Decimal
from app.database.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.cashflow import CashFlowGroupBy, AggregatedCashFlowResponse
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.schemas.dashboard import SummaryResponse, CategoryPeriodAmount
from typing import Optional, List
from datetime import date, timedelta, datetime

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("/balance-timeline")
def get_balance_timeline(
    group_by: str = Query("day", regex="^(day|month|quarter)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает временной ряд доходов, расходов и баланса за период.
    group_by: day, month, quarter
    """
    # Базовый запрос с группировкой по выбранному интервалу
    query = db.query(
        func.date_trunc(group_by, Transaction.date).label("period"),
        func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label("income"),
        func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label("expense")
    ).filter(Transaction.user_id == current_user.id)

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    results = query.group_by("period").order_by("period").all()

    # Преобразуем в список словарей для удобного использования на фронте
    timeline = []
    for period, income, expense in results:
        # date_trunc возвращает datetime, приводим к дате для JSON
        period_date = period.date() if isinstance(period, datetime) else period
        timeline.append({
            "period": period_date.isoformat(),
            "income": float(income) if income else 0,
            "expense": float(expense) if expense else 0,
            "balance": (income or 0) - (expense or 0)
        })
    return timeline

@router.get("/cash-flow/summary")
def get_cash_flow_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_ids: Optional[List[int]] = Query(None),
    group_by: str = Query(..., regex="^(day|month|quarter)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Получаем все категории пользователя (для маппинга id -> name)
    user_categories = db.query(Category.id, Category.name).filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).all()
    cat_name_map = {cat_id: name for cat_id, name in user_categories}

    # 2. Строим агрегирующий запрос
    query = db.query(
        func.date_trunc(group_by, Transaction.date).label("period_trunc"),
        Transaction.category_id,
        func.sum(case((Transaction.transaction_type == 'income', Transaction.amount), else_=0)).label("income"),
        func.sum(case((Transaction.transaction_type == 'expense', Transaction.amount), else_=0)).label("expense")
    ).join(Category, Transaction.category_id == Category.id).filter(
        Transaction.user_id == current_user.id
    )

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category_ids:
        query = query.filter(Category.id.in_(category_ids))

    query = query.group_by("period_trunc", Transaction.category_id).order_by("period_trunc")

    results = query.all()

    # 3. Собираем результат в удобную структуру
    periods = {}
    for period_trunc, cat_id, inc, exp in results:
        # Преобразуем timestamp в строку ISO даты (без времени)
        if isinstance(period_trunc, datetime):
            period_key = period_trunc.date().isoformat()
        else:
            period_key = period_trunc.isoformat()

        if period_key not in periods:
            periods[period_key] = {
                "period": period_key,
                "income": 0,
                "expense": 0,
                "net": 0,
                "categories": []
            }

        periods[period_key]["income"] += inc or 0
        periods[period_key]["expense"] += exp or 0

        # Добавляем категорию
        cat_name = cat_name_map.get(cat_id, "—")
        periods[period_key]["categories"].append({
            "category_id": cat_id,
            "category_name": cat_name,
            "income": inc or 0,
            "expense": exp or 0,
            "net": (inc or 0) - (exp or 0)
        })

    # Вычисляем net для каждого периода
    for period_data in periods.values():
        period_data["net"] = period_data["income"] - period_data["expense"]
        # Сортируем категории по имени (опционально)
        period_data["categories"].sort(key=lambda x: x["category_name"])

    # Преобразуем словарь в список, отсортированный по дате
    result = sorted(periods.values(), key=lambda x: x["period"])
    return result

@router.get("/aggregated", response_model=SummaryResponse)
def get_aggregated(
    months: int = Query(1, ge=1, le=24, description="Количество месяцев для агрегации"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает сводку по транзакциям за указанный период (months назад от сегодня),
    а также общую статистику за всё время (если start_date/end_date не заданы).
    Если start_date и end_date заданы, игнорирует months.
    """
    # Базовый запрос всех транзакций пользователя
    base_query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    # Определяем период для агрегации
    if start_date and end_date:
        # Пользователь явно задал даты – используем их
        period_start = start_date
        period_end = end_date
    else:
        # Используем months назад от сегодня
        period_end = date.today()
        period_start = period_end - timedelta(days=30 * months)  # упрощённо, но достаточно

    period_query = base_query.filter(
        Transaction.date >= period_start,
        Transaction.date <= period_end
    )

    # Общая статистика за весь период (независимо от выбранного)
    total_income_all = base_query.filter(Transaction.transaction_type == 'income').with_entities(func.sum(Transaction.amount)).scalar() or Decimal(0)
    total_expense_all = base_query.filter(Transaction.transaction_type == 'expense').with_entities(func.sum(Transaction.amount)).scalar() or Decimal(0)
    balance_all = total_income_all - total_expense_all

    # Статистика за выбранный период
    total_income_period = period_query.filter(Transaction.transaction_type == 'income').with_entities(func.sum(Transaction.amount)).scalar() or Decimal(0)
    total_expense_period = period_query.filter(Transaction.transaction_type == 'expense').with_entities(func.sum(Transaction.amount)).scalar() or Decimal(0)

    # Разбивка по категориям за период
    results = (
        db.query(
            Category.id,
            Category.name,
            Category.category_type,
            func.sum(Transaction.amount).label('total')
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(Transaction.user_id == current_user.id)
        .filter(Transaction.date >= period_start, Transaction.date <= period_end)
        .group_by(Category.id, Category.name, Category.category_type)
        .all()
    )

    incomes = []
    expenses = []
    for cat_id, name, cat_type, total in results:
        if cat_type == 'income':
            incomes.append(CategoryPeriodAmount(category_id=cat_id, category_name=name, amount=total))
        else:
            expenses.append(CategoryPeriodAmount(category_id=cat_id, category_name=name, amount=total))

    period_breakdown = {"income": incomes, "expense": expenses}

    return SummaryResponse(
        balance=balance_all,
        total_income=total_income_all,
        total_expense=total_expense_all,
        period_balance=total_income_period - total_expense_period,
        period_total_income=total_income_period,
        period_total_expense=total_expense_period,
        period_breakdown=period_breakdown,
        period_start=period_start,
        period_end=period_end
    )

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    # сортировка по дате (сначала новые)
    query = query.order_by(Transaction.date.desc())
    transactions = query.offset(skip).limit(limit).all()
    return transactions

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем, что категория существует и принадлежит пользователю или системная
    category = db.query(Category).filter(
        Category.id == transaction_data.category_id,
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or not accessible"
        )

    # Проверяем соответствие типа транзакции и типа категории
    if transaction_data.transaction_type != category.category_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction type must match category type"
        )

    new_transaction = Transaction(
        **transaction_data.model_dump(),
        user_id=current_user.id
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Если обновляется категория, проверяем доступность и соответствие типа
    if transaction_data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == transaction_data.category_id,
            (Category.user_id == current_user.id) | (Category.user_id.is_(None))
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or not accessible"
            )
        # Если тип транзакции не меняется, проверяем соответствие
        # type не обновляется, поэтому используем текущий тип транзакции
        if transaction.transaction_type != category.category_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category type must match transaction type"
            )
        transaction.category_id = transaction_data.category_id

    # Обновляем другие поля, если они переданы
    update_data = transaction_data.model_dump(exclude_unset=True, exclude={"category_id"})
    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    db.delete(transaction)
    db.commit()

