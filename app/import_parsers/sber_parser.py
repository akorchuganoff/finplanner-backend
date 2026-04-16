import fitz  # PyMuPDF
import re
from datetime import datetime
from decimal import Decimal

def parse_sber_pdf(file_path):
    date_pattern = re.compile(r'^(\d{2}\.\d{2}\.\d{4})')
    time_pattern = re.compile(r'^(\d{2}:\d{2})')
    star_pattern = re.compile(r'\*\*\*\*')
    transactions = []

    doc = fitz.open(file_path)
    full_text = []
    for page in doc:
        text = page.get_text()
        full_text.append(text)
    doc.close()

    all_text = '\n'.join(full_text)
    lines = all_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if date_pattern.match(line) and time_pattern.match(lines[i+1].strip()):
            transaction_lines = [line]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                transaction_lines.append(next_line)
                if star_pattern.search(next_line):
                    i += 1
                    break
                i += 1

            if i >= len(lines):
                continue
            print(transaction_lines)

            date_str = transaction_lines[0]
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
            bank_category = transaction_lines[2]
            amount_str = transaction_lines[3].replace("\xa0", '').replace(" ", '').replace(',', '.')
            if amount_str.startswith('+'):
                ttype = 'income'
                amount = Decimal(amount_str[1:])
            else:
                ttype = 'expense'
                amount = Decimal(amount_str)

            description = transaction_lines[-1]

            transactions.append({
                'date': date_obj,
                'amount': amount,
                'type': ttype,
                'description': description,
                'bank_category': bank_category
            })
        else:
            i += 1

    return transactions