import pdfplumber
import re
from datetime import datetime
from decimal import Decimal

def parse_tbank_pdf(file_path):
    transactions = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                # Пример: ['07.04.2026 06:01', '08.04.2026 16:56', '-1 999.70 ₽', '-1 999.70 ₽', 'Оплата в RNAZK 10 ALNP BIYSK RUS', '1262']
                if len(row) < 6:
                    continue
                date_str = row[0]
                amount_str = row[2].replace('₽', '').replace(' ', '').replace(',', '.')
                desc = row[4]
                if amount_str.startswith('-'):
                    ttype = 'expense'
                    amount = Decimal(amount_str[1:])
                elif amount_str.startswith('+'):
                    ttype = 'income'
                    amount = Decimal(amount_str[1:])
                else:
                    continue
                date = datetime.strptime(date_str.split()[0], '%d.%m.%Y').date()
                transactions.append({
                    'date': date,
                    'amount': amount,
                    'type': ttype,
                    'description': desc,
                    'bank_category': None
                })
    return transactions