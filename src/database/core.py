from os.path import join, dirname
from dotenv import load_dotenv
import os 
from supabase import Client, create_client
from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends

dotenv_path = 'src/.env'
load_dotenv(dotenv_path)

# HOST_DB = os.getenv("HOST_DB")
# NAME_DB = os.getenv("NAME_DB")
# USER_DB = os.getenv("USER_DB")
# PASSWORD_DB = os.getenv("PASSWORD_DB")
# PORT_DB = os.getenv("PORT_DB")

# URL_DATABASE = f'postgresql://{USER_DB}:{PASSWORD_DB}@{HOST_DB}:{PORT_DB}/expense'

# engine = create_engine(URL_DATABASE)

# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base = declarative_base()

# def connect_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# DBSession = Annotated[Session, Depends(connect_db)]
def connect_db():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    db: Client = create_client(SUPABASE_URL,SUPABASE_KEY)
    return db

DBSession = Annotated[Client, Depends(connect_db)]