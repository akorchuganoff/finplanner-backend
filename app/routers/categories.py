from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from app.database.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    category_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить список категорий пользователя (системные + свои).
    Если указан category_type, фильтруем по типу.
    """
    query = db.query(Category).filter(
        (Category.user_id == current_user.id) | (Category.user_id.is_(None))
    )
    if category_type:
        query = query.filter(Category.category_type == category_type)
    categories = query.order_by(Category.category_type, Category.name).all()
    return categories

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новую пользовательскую категорию.
    Проверяем, нет ли уже категории с таким именем и типом у пользователя.
    """
    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name == category_data.name,
        Category.category_type == category_data.category_type
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name and category_type already exists for this user"
        )

    new_category = Category(
        name=category_data.name,
        category_type=category_data.category_type,
        user_id=current_user.id
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить название своей категории. Системные категории нельзя редактировать.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    # Системная категория (user_id is None) – нельзя редактировать
    if category.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system category"
        )
    # Проверяем, что категория принадлежит текущему пользователю
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this category"
        )

    # Проверка на дублирование имени (если меняется имя)
    if category_update.name and category_update.name != category.name:
        existing = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.category_type == category.category_type,
            Category.name == category_update.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name and category_type already exists for this user"
            )
        category.name = category_update.name

    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить свою категорию. Системные категории нельзя удалить.
    Проверка, что категория не используется в транзакциях (если есть транзакции – запретить).
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system category"
        )
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this category"
        )

    # Проверка на наличие связанных транзакций (пока транзакции нет, заглушка)
    # В будущем: if category.transactions: raise ...
    # Пока просто удаляем

    db.delete(category)
    db.commit()
    return