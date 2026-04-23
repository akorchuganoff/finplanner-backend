from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.utils.hash import generate_transaction_hash
from decimal import Decimal
from datetime import date
from typing import Optional

def create_transaction_if_not_exists(
    db: Session,
    user_id: int,
    category_id: int,
    amount: Decimal,
    transaction_type: str,
    date: date,
    comment: str = ""
) -> Optional[Transaction]:
    tx_hash = generate_transaction_hash(user_id, date, amount, transaction_type, comment)
    existing = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.unique_hash == tx_hash
    ).first()
    print("Filter response worked correctly")
    if existing:
        return None
    new_tx = Transaction(
        amount=amount,
        transaction_type=transaction_type,
        date=date,
        comment=comment,
        user_id=user_id,
        category_id=category_id,
        unique_hash=tx_hash
    )
    db.add(new_tx)
    return new_tx



def update_transaction_if_no_conflict(
    db: Session,
    transaction: Transaction,
    user_id: int,
    new_amount: Optional[Decimal] = None,
    new_type: Optional[str] = None,
    new_date: Optional[date] = None,
    new_comment: Optional[str] = None,
) -> Transaction:
    """
    Обновляет транзакцию и пересчитывает хеш.
    Если новое сочетание полей уже существует у другой транзакции, возвращает None.
    """
    # Сохраняем старые значения для полей, которые могут не измениться
    amount = new_amount if new_amount is not None else transaction.amount
    tx_type = new_type if new_type is not None else transaction.transaction_type
    date_val = new_date if new_date is not None else transaction.date
    comment = new_comment if new_comment is not None else transaction.comment

    # Генерируем новый хеш
    new_hash = generate_transaction_hash(user_id, date_val, amount, tx_type, comment)
    print(new_hash)
    # Проверяем, нет ли другой транзакции с таким же хешем
    existing = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.unique_hash == new_hash,
        Transaction.id != transaction.id
    ).first()
    if existing:
        return None

    # Обновляем поля
    transaction.amount = amount
    transaction.transaction_type = tx_type
    transaction.date = date_val
    transaction.comment = comment
    transaction.unique_hash = new_hash
    return transaction