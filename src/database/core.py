from os.path import join, dirname
from dotenv import load_dotenv
import os 
# from supabase import Client, create_client
from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends

dotenv_path = 'src/.env'
load_dotenv(dotenv_path)

URL_DATABASE = 'postgresql://postgres:12345@localhost:5432/expense'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def connect_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBSession = Annotated[Session, Depends(connect_db)]
# def connect_db():
#     SUPABASE_URL = os.getenv("SUPABASE_URL")
#     SUPABASE_KEY = os.getenv("SUPABASE_KEY")
#     db: Client = create_client(SUPABASE_URL,SUPABASE_KEY)
#     return db

# DbSession = Annotated[Client, Depends(connect_db)]