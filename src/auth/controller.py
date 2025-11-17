from .model import RegisterUserRequest
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends
from ..auth import service
from ..database.core import connect_db
import logging
router = APIRouter()
# Create data model user

@router.post("/register/", tags=["users"])
def register(user: RegisterUserRequest):
    db = connect_db()
    return service.create_user(db, user)

@router.post('/login/', tags=["users"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = connect_db()
    return service.login(db, form_data)
