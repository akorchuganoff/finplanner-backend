import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.database import SessionLocal
from app.models.transaction import Transaction
from app.utils.hash import generate_transaction_hash
from collections import defaultdict

def deduplicate():
    db = SessionLocal()
    transactions = db.query(Transaction).all()
    groups = defaultdict(list)
    for tx in transactions:
        # Временно генерируем хеш (поле unique_hash может быть пустым)
        description = tx.comment or ""
        h = generate_transaction_hash(tx.user_id, tx.date, tx.amount, tx.transaction_type, description)
        groups[h].append(tx)

    deleted = 0
    for h, txs in groups.items():
        if len(txs) > 1:
            # Оставляем одну транзакцию (например, самую новую по id)
            txs.sort(key=lambda x: x.id, reverse=True)
            keep = txs[0]
            for dup in txs[1:]:
                db.delete(dup)
                deleted += 1
            # Устанавливаем хеш для оставшейся
            keep.unique_hash = h
            db.add(keep)
        else:
            txs[0].unique_hash = h
            db.add(txs[0])
    db.commit()
    print(f"Удалено дубликатов: {deleted}")
    db.close()

if __name__ == "__main__":
    deduplicate()