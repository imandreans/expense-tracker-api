from pydantic import BaseModel,Field
import datetime
from uuid import UUID, uuid4
from enum import Enum

class CategoryExpense(Enum):
    GROCERIES = "Groceries"
    LEISURE = "Leisure"
    ELECTRONICS = "Electronics"
    UTILIES = "Utilies"
    CLOTHING = "Clothing"
    HEALTH = "Health"
    OTHERS = "Others"

class CreateExpense(BaseModel):
    # Field type must be ...
    id: UUID = Field(default_factory=uuid4, frozen=True)
    #the title must not empty
    title: str = Field(min_length=1)
    #price must be a positive values
    price: int = Field(gt=0)
    category: CategoryExpense
    # 
    date: datetime.datetime = datetime.datetime.now()

