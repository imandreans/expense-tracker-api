from supabase import Client
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, HTTPException
from .model  import RegisterUserRequest, Token, TokenData
import datetime
from passlib.context import CryptContext
import uuid
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
def authenticate_user(username: str, password: str, db: Client) -> list:
    user = db.table("Users").select("*").eq("username", username).execute()
    if user.data == [] or not verify_password(password, user.data[0]["password"]):
        logging.error("Username/Password is invalid")
        raise HTTPException(status_code=400, detail="Username/Password is invalid!")
    return user.data[0]

def create_access_token(username: str, user_id: str, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expires_delta = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
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
    except InvalidTokenError:
         logging.error("Token invalid")
         raise credentials_exception
    return token_data

security = HTTPBearer()

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    logging.info("Getting current user...")
    return verify_token(token.credentials)


def create_user(db: Client, request: RegisterUserRequest) -> Token:
            username = request.username
            password = request.password 
            balance = request.balance
            try:
                logging.info("Getting user data from db...")
                user = db.table("Users").select("*").eq("username", username).execute()
                if user.data != []:
                    logging.error("Username conflict with another username")
                    raise HTTPException(status_code=409, detail="User already exists")
                
                new_id = str(uuid.uuid4())
                logging.info("Getting user data from db...")
                db.table("Users").insert({"id": new_id,
                                        "username": username,
                                        "password": hash_password(password),
                                        "balance": balance}).execute()
                # Create access token can wait, 
                token = create_access_token(username, new_id, datetime.timedelta(minutes=10))
                return Token(create_access=token, token_type="bearer") 
            except Exception as e:
                 logging.error(str(e))
                 raise HTTPException(status_code=500, detail=str(e))
        
        
CurrentUser = Annotated[TokenData, Depends(get_current_user)]

def login(db: Client, request: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    username = request.username
    password = request.password
    
    user = authenticate_user(username, password, db)
    token = create_access_token(username, user["id"], 
                            datetime.timedelta(minutes=10))
    logging.info("User logged in")
    return Token(create_access=token, token_type="bearer")

