from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.import_parsers import parse_sber_pdf, parse_tbank_pdf
from app.utils.categorizer import suggest_category
from app.utils.hash import generate_transaction_hash 
from app.services.transaction_service import create_transaction_if_not_exists
from app.models.category import Category
from app.models.transaction import Transaction

from datetime import datetime

from typing import List

router = APIRouter(prefix="/api/import", tags=["import"])

@router.post("/upload")
async def import_bank_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Сохраняем файл временно
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Определяем банк по имени файла или содержимому
    if "сбер" in file.filename.lower() or "sber" in file.filename.lower():
        print("SBER")
        raw_transactions = parse_sber_pdf(file_path)
    elif "tbank" in file.filename.lower() or "t-bank" in file.filename.lower():
        raw_transactions = parse_tbank_pdf(file_path)
        print("TBANK")
    else:
        raise HTTPException(400, "Неизвестный формат выписки")

    user_categories_map = {}
    db_categories = db.query(Category).filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    ).all()
    for cat in db_categories:
        user_categories_map[(cat.name, cat.category_type)] = cat.id


    # Для каждой транзакции подбираем категорию
    suggested = []
    for tx in raw_transactions:
        cat_name, cat_type = suggest_category(
            tx['description'], tx['amount'], tx['type'], tx.get('bank_category')
        )
        category_id = user_categories_map.get((cat_name, cat_type), None)
        
        tx_hash = generate_transaction_hash(
            user_id=current_user.id,
            date=tx['date'],
            amount=tx['amount'],
            transaction_type=tx['type'],
            description=tx['description']
        )
        existing_tx = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.unique_hash == tx_hash
        ).first()
        is_duplicate = existing_tx is not None
        
        suggested.append({
            **tx,
            'suggested_category_id': category_id,
            'suggested_category_name': cat_name,
            'is_duplicate': is_duplicate,
        })

    return {"transactions": suggested, "total": len(suggested)}


@router.post("/confirm")
def confirm_import(
    transactions_data: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    duplicates_amount = 0
    created = []
    for tx_data in transactions_data:
        # В данных обязательно должен быть category_id (пользователь мог исправить)
        category_id = tx_data.get('category_id')
        if not category_id:
            continue
        new_tx = create_transaction_if_not_exists(
            db=db,
            user_id=current_user.id,
            category_id=category_id,
            amount=tx_data['amount'],
            transaction_type=tx_data['type'],
            date=datetime.strptime(tx_data['date'], "%Y-%m-%d"),
            comment=tx_data.get('description', '')
        )
        if new_tx:
            created.append(new_tx)
        else:
            duplicates_amount += 1
    db.commit()
    return {"imported": len(created), "duplicates": duplicates_amount, "transactions": created}