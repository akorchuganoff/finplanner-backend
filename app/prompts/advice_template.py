from decimal import Decimal
from typing import Dict, Any

def format_currency(amount: Decimal) -> str:
    return f"{amount:,.2f}"

def format_top_categories(categories: list, limit: int = 3) -> str:
    if not categories:
        return "—"
    items = categories[:limit]
    return ", ".join([f"{cat['name']} ({format_currency(cat['amount'])} ₽)" for cat in items])

def build_advice_prompt(analytics: Dict[str, Any]) -> str:
    short = analytics.get('short', {})
    medium = analytics.get('medium', {})
    long_term = analytics.get('long', {})

    prompt = f"""
Ты — опытный персональный финансовый консультант. Проанализируй следующие данные о финансах пользователя за три периода: последние 2 недели (краткосрочный), последние 3 месяца (среднесрочный) и последний год (долгосрочный). На основе этих данных дай пользователю **3–5 конкретных, практических советов** по оптимизации бюджета, сокращению расходов и улучшению финансового здоровья. Советы должны быть краткими, по делу, без воды. Учитывай долгосрочные тренды и повторяющиеся паттерны. Если заметны сезонные колебания или рост/падение доходов/расходов, отметь это.

### Краткосрочный период (последние 2 недели):
- Доходы: {format_currency(short.get('income', 0))} ₽
- Расходы: {format_currency(short.get('expense', 0))} ₽
- Баланс (прирост/убыток): {format_currency(short.get('balance', 0))} ₽
- Средний расход в день: {format_currency(short.get('avg_daily_expense', 0))} ₽
- Топ категории доходов: {format_top_categories(short.get('top_income_categories', []))}
- Топ категории расходов: {format_top_categories(short.get('top_expense_categories', []))}

### Среднесрочный период (последние 3 месяца):
- Доходы: {format_currency(medium.get('income', 0))} ₽
- Расходы: {format_currency(medium.get('expense', 0))} ₽
- Баланс: {format_currency(medium.get('balance', 0))} ₽
- Средний расход в день: {format_currency(medium.get('avg_daily_expense', 0))} ₽
- Топ категории доходов: {format_top_categories(medium.get('top_income_categories', []))}
- Топ категории расходов: {format_top_categories(medium.get('top_expense_categories', []))}

### Долгосрочный период (последний год):
- Доходы: {format_currency(long_term.get('income', 0))} ₽
- Расходы: {format_currency(long_term.get('expense', 0))} ₽
- Баланс: {format_currency(long_term.get('balance', 0))} ₽
- Средний расход в день: {format_currency(long_term.get('avg_daily_expense', 0))} ₽
- Топ категории доходов: {format_top_categories(long_term.get('top_income_categories', []))}
- Топ категории расходов: {format_top_categories(long_term.get('top_expense_categories', []))}

### Помесячная динамика (последние 12 месяцев):
"""
    # Добавим помесячную динамику, если есть
    monthly = analytics.get('monthly_timeline', [])
    if monthly:
        prompt += "\n| Месяц | Доходы | Расходы | Баланс |\n|-------|--------|---------|--------|\n"
        for m in monthly:  # последние 12 месяцев
            prompt += f"| {m['month']} | {format_currency(m['income'])} | {format_currency(m['expense'])} | {format_currency(m['balance'])} |\n"
    else:
        prompt += "\nНет данных по месяцам.\n"

    prompt += """

Теперь дай чёткие, приоритетные рекомендации в виде нумерованного списка. Сфокусируйся на практических шагах, которые пользователь может предпринять сразу.
"""
    return prompt