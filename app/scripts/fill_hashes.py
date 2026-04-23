import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.database.database import SessionLocal
from app.models.transaction import Transaction
from app.utils.hash import generate_transaction_hash

def run():
    db = SessionLocal()
    txs = db.query(Transaction).filter(Transaction.unique_hash.is_(None)).all()
    for tx in txs:
        description = tx.comment or ""
        tx.unique_hash = generate_transaction_hash(tx.user_id, tx.date, tx.amount, tx.transaction_type, description)
    db.commit()
    print(f"Updated {len(txs)} transactions")

if __name__ == '__main__':
    run()