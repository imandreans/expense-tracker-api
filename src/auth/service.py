# from supabase import Client
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException
from .model  import RegisterUserRequest, Token, TokenData
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import uuid
from ..entities.core import User
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated
import logging

from dotenv import load_dotenv
import os
# from fastapi import HTTPException, status
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
load_dotenv("src/.env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

def hash_password(password: str) -> str:
    logging.info("Hashed password")
    return bcrypt_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> str:
    logging.info("Verified Password")
    return bcrypt_context.verify(plain_password, hashed_password)

# Error handling working
def authenticate_user(username: str, password: str, db: Session) -> list:
    query = select(User).where(User.username == username)
    user = db.scalars(query).first()
    # user = db.table("Users").select("*").eq("username", username).execute()
    if user or verify_password(password, user.password):
        return user.id
    logging.error("Username/Password is invalid")
    raise HTTPException(status_code=400, detail="Username/Password is invalid!")

def create_access_token(username: str, user_id: str, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=30)
    encode = {"exp": expires_delta, "id": user_id, "sub": username}
    logging.info("Token is created")
    return jwt.encode(encode, JWT_SECRET_KEY, JWT_ALGORITHM)



def verify_token(token) -> TokenData:
    credentials_exception = HTTPException(status_code=401,
                                          detail="Could not validate credentials",
                                          headers={"WWW-Authenticate" : "Bearer"})
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
        user_id: str = payload.get('id')
        logging.info("Token is decoded")
        if user_id == "":
             logging.error("Credentials invalid")
             raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except Exception as e:
         logging.error(f"Token invalid: {e}")
         raise credentials_exception
    return token_data

security = HTTPBearer()

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    logging.info("Getting current user...")
    return verify_token(token.credentials)


def create_user(db: Session, request: RegisterUserRequest) -> Token | None:
    try:

        query = select(User).where(User.username == request.username)
        user = db.scalars(query).first()
        logging.info(f"Getting {request.username}, if already exists")
        if user:
            raise HTTPException(status_code=409, detail="Username has already exists")
        
        logging.info(f"Create new username. . .")
        new_user = User(
            id=uuid.uuid4(),
            username=request.username,
            password = hash_password(request.password),
            balance = request.balance,
        )
        
        # db = next(db) # do this because there's error said 'generator doesn't have add attributes'
        db.add(new_user)
        db.commit()
        
        token = create_access_token(new_user.username, new_user.id, timedelta(minutes=10))
        return Token(create_access=token, type="bearer") 
    except Exception as e:
        logging.error(f"Failed to register user: {e}")
        raise
        
        
CurrentUser = Annotated[TokenData, Depends(get_current_user)]

def login(db: Session, request: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    username = request.username
    password = request.password
    
    user = authenticate_user(username, password, db)
    token = create_access_token(username, str(user), 
                            timedelta(minutes=10))
    logging.info("User logged in")
    return Token(create_access=token, token_type="bearer")

