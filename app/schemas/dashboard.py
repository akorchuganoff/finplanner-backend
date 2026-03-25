from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional

class CategoryPeriodAmount(BaseModel):
    category_id: int
    category_name: str
    amount: Decimal

class PeriodBreakdown(BaseModel):
    income: List[CategoryPeriodAmount] = []
    expense: List[CategoryPeriodAmount] = []

class SummaryResponse(BaseModel):
    balance: Decimal                     # общий баланс (все транзакции)
    total_income: Decimal                # общий доход (все транзакции)
    total_expense: Decimal               # общий расход (все транзакции)
    period_balance: Decimal              # баланс за выбранный период
    period_total_income: Decimal         # доход за период
    period_total_expense: Decimal        # расход за период
    period_breakdown: PeriodBreakdown    # разбивка по категориям за период
    period_start: date                   # начало периода
    period_end: date                     # конец периода