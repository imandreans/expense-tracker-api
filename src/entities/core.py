from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from ..database.core import Base
import enum

class User(Base):
    __tablename__ = 'users'

    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # username = Column(String, nullable=False)
    # password = Column(String, nullable=False)
    # balance = Column(Integer, nullable=False, default=0)
    # created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60))
    password: Mapped[str]
    balance: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    expenses: Mapped[list["Expense"]] = relationship(back_populates="user")
    def __repr__(self):
        return f'<User(name={self.username}, balance={self.password})>'
    
class Category(enum.Enum):
    GROCERIES = "Groceries"
    LEISURE = "Leisure"
    ELECTRONICS = "Electronics"
    UTILIES = "Utilies"
    CLOTHING = "Clothing"
    HEALTH = "Health"
    OTHERS = "Others"

class Expense(Base):
    __tablename__ = 'expenses'
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    # title = Column(String, nullable=False)
    # price = Column(Integer, nullable=False, default=0)
    # category = Column(Enum(Category), nullable=False, default=Category.OTHERS.value)
    # created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(60))
    price: Mapped[int] = mapped_column(default=0)
    category: Mapped[Category] = mapped_column(default=Category.OTHERS.value)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped[list["User"]] = relationship(back_populates="expenses")
    def __repr__(self):
        return f'<User(title={self.title}, price={self.price}, category={self.category}, created_at={self.created_at})>'