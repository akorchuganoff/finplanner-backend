import re
from datetime import datetime
from decimal import Decimal

# Словарь ключевых слов -> (имя категории, тип)
# Позже можно вынести в БД и дать пользователю настраивать.
KEYWORD_RULES = [
    (re.compile(r'PYATEROCHKA|MAGNIT|ЛЕНТА|КРАСНОЕ&БЕЛОЕ|MARIYA-RA|YARCHE', re.I), 'Продукты', 'expense'),
    (re.compile(r'GAZPROMNEFT|АЗС|AIA\*Gazprom', re.I), 'Транспорт', 'expense'),
    (re.compile(r'Wildberries|OZON|WB\*', re.I), 'Онлайн-покупки', 'expense'),
    (re.compile(r'Перевод|Перевод СБП|Внутрибанковский перевод', re.I), 'Переводы', None),  # тип определим по сумме
    (re.compile(r'Рестораны|кафе|GRILNICA|ROSTICS', re.I), 'Рестораны', 'expense'),
    (re.compile(r'Доход|Зарплата|Кэшбэк', re.I), 'Доход', 'income'),
]

def map_bank_category(bank_category: str) -> tuple:
    """Маппинг категорий Сбера на наши категории"""
    mapping = {
        'Супермаркеты': ('Продукты', 'expense'),
        'Одежда и аксессуары': ('Одежда', 'expense'),
        'Рестораны и кафе': ('Рестораны', 'expense'),
        'Прочие операции': (None, None),
    }
    return mapping.get(bank_category, (None, None))

def suggest_category(description: str, amount: Decimal, ttype: str, bank_category: str = None):
    # 1. Если есть категория банка
    if bank_category:
        cat_name, cat_type = map_bank_category(bank_category)
        if cat_name:
            return cat_name, cat_type
    # 2. Правила по ключевым словам
    for pattern, cat_name, cat_type in KEYWORD_RULES:
        if pattern.search(description):
            # Если тип не указан в правиле, берём из транзакции
            final_type = cat_type if cat_type else ttype
            return cat_name, final_type
        if pattern.search(bank_category):
            # Если тип не указан в правиле, берём из транзакции
            final_type = cat_type if cat_type else ttype
            return cat_name, final_type
    # 3. Не определили
    return None, None