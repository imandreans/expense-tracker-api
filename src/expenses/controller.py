from fastapi import APIRouter
from . import service
from ..auth.service import CurrentUser
from .model import CreateExpense
from ..database.core import DbSession

router = APIRouter(
    prefix="/expense",
    tags=["Expenses"]
)

@router.post('/add/')
def add_expense(db: DbSession, current_user: CurrentUser, expense: CreateExpense):
    return service.create_expenses(db, current_user, expense)

@router.delete('/delete/<id>')
def delete_expense(db: DbSession,current_user: CurrentUser, id):
    return service.delete_expense(db, current_user, id)

@router.patch('/edit/<id>')
def edit_expense(db: DbSession,current_user: CurrentUser, id, expense: CreateExpense):
    return service.edit_expense(db, current_user, id, expense)

@router.get("/")
def list_expenses(db: DbSession, current_user: CurrentUser):
    return service.list_all_expenses(db, current_user)