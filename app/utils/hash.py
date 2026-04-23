import hashlib
import re
from datetime import date
from decimal import Decimal

def normalize_description(desc: str) -> str:
    desc = desc.lower()
    desc = re.sub(r'[^a-zа-я0-9\s]', '', desc)
    desc = re.sub(r'\b\d{6}\b', '', desc)       # убираем коды авторизации
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc

def generate_transaction_hash(user_id: int, date: date, amount: Decimal, transaction_type: str, description: str) -> str:
    norm_desc = normalize_description(description)
    signed_amount = f"+{amount}" if transaction_type == 'income' else f"-{amount}"
    unique_str = f"{user_id}|{date.isoformat()}|{signed_amount}|{norm_desc}"
    return hashlib.sha256(unique_str.encode('utf-8')).hexdigest()