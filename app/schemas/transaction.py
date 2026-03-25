from pydantic import BaseModel, Field, condecimal
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal
from datetime import date as date_type

class TransactionBase(BaseModel):
    amount: condecimal(max_digits=10, decimal_places=2) = Field(..., gt=0)
    transaction_type: Literal['income', 'expense']
    date: date_type = Field(default_factory=date_type.today)
    comment: Optional[str] = None
    category_id: int

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(None, gt=0)
    date: Optional[date_type] = None
    comment: Optional[str] = None
    category_id: Optional[int] = None
    # type менять нельзя, иначе нарушится соответствие с категорией

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True