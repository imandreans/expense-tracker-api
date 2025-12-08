from .model import RegisterUserRequest
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, status
from ..auth import service
from ..database.core import connect_db
router = APIRouter()
# Create data model user

@router.post("/register/", tags=["users"], status_code=status.HTTP_201_CREATED)
def register(user: RegisterUserRequest):
    db = connect_db()
    return service.create_user(db, user)

@router.post('/login/', tags=["users"], status_code=status.HTTP_202_ACCEPTED)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = connect_db()
    return service.login(db, form_data)
