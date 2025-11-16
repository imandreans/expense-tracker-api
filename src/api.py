from fastapi import FastAPI
from src.auth.controller import router as auth_router
from src.expenses.controller import router as expense_router

def register_routers(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(expense_router)
    