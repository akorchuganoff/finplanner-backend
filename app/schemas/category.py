from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.category import CategoryType

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: CategoryType

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)

class CategoryResponse(CategoryBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True