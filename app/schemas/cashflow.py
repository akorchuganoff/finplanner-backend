from pydantic import BaseModel
from typing import Optional
import enum

class CashFlowGroupBy(str, enum.Enum):
    day = "day"
    month = "month"
    quarter = "quarter"
    category = "category"

class AggregatedCashFlowResponse(BaseModel):
    # Для day/month/quarter
    period: Optional[str] = None
    income_total: Optional[float] = None
    expense_total: Optional[float] = None
    net: Optional[float] = None
    # Для category
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_type: Optional[str] = None
    total_amount: Optional[float] = None

    class Config:
        from_attributes = True