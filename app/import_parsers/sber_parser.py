import pdfplumber
import re
from datetime import datetime
from decimal import Decimal

def parse_sber_pdf(file_path):
    transactions = []

    rows = []
    with pdfplumber.open(file_path, repair=True) as pdf:
        all_text = ''
        for page in pdf.pages:
            text = page.extract_text()

            all_text += text + "\n"
        
        rows += all_text.split('\n')
    


    # Оставляем только транзакции
    transactions = []
    current_transaction_data = []

    for row in rows:
        print(row)

        if "****" in row:
            current_transaction_data.append(row)
            transactions.append(current_transaction_data)
            current_transaction_data = []
        elif bool(re.match(r'^(?:\d{2}\.\d{2}\.\d{4})', row)):
            current_transaction_data.append(row)
        else:
            current_transaction_data = []

    print(transactions)

    parsed_transactions = []
    for row in transactions:
        l1 = row[0]
        if len(row)==3:
            l2 = row[1]+row[2]
        else:
            l2 = row[1]

        data = l1.split(" ")
        date = datetime.strptime(data[0], '%d.%m.%Y').date()

        time = data[1]

        ostatok = " ".join(data[2:])
        
        i = 0

        while ostatok[i] not in '+0123456789':
            i += 1
        bank_category = ostatok[:i]

        amount_index = i
        while ostatok[i] != ',':
            i += 1
        amount_str = ostatok[amount_index:i+2].replace(',', '.').replace(' ','')

        if amount_str[0].startswith('+'):
            ttype='income'
            amount=Decimal(amount_str)
        else:
            ttype='expense'
            amount=Decimal("-"+amount_str)

        l2_data = l2.split(' ')
        transaction_code = l2_data[1]
        description = " ".join(l2_data[2:])

        parsed_transactions.append({
            'date': date,
            'amount': amount,
            'type': ttype,
            'description': description,
            'bank_category': bank_category
        })

    return parsed_transactions