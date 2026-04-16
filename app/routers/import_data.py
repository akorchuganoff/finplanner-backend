from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.import_parsers import parse_sber_pdf, parse_tbank_pdf
from app.import_utils.categorizer import suggest_category
from app.models.category import Category
from app.models.transaction import Transaction

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



    # Для каждой транзакции подбираем категорию
    suggested = []
    for tx in raw_transactions:
        cat_name, cat_type = suggest_category(
            tx['description'], tx['amount'], tx['type'], tx.get('bank_category')
        )
        category_id = None
        if cat_name:
            # Ищем существующую категорию пользователя или системную
            category = db.query(Category).filter(
                Category.name == cat_name,
                Category.category_type == cat_type,
                (Category.user_id == current_user.id) | (Category.user_id.is_(None))
            ).first()
            if category:
                category_id = category.id
        suggested.append({
            **tx,
            'suggested_category_id': category_id,
            'suggested_category_name': cat_name,
        })
    
    return {"transactions": suggested, "total": len(suggested)}


@router.post("/confirm")
def confirm_import(
    transactions_data: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = []
    for tx_data in transactions_data:
        # В данных обязательно должен быть category_id (пользователь мог исправить)
        category_id = tx_data.get('category_id')
        if not category_id:
            continue
        new_tx = Transaction(
            amount=tx_data['amount'],
            transaction_type=tx_data['type'],
            date=tx_data['date'],
            comment=tx_data.get('comment', ''),
            user_id=current_user.id,
            category_id=category_id,
        )
        db.add(new_tx)
        created.append(new_tx)
    db.commit()
    return {"imported": len(created)}