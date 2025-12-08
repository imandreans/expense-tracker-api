from os.path import join, dirname
from dotenv import load_dotenv
import os 
# from supabase import Client, create_client
from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from fastapi import Depends

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

URL_DATABASE = os.getenv("URL_DATABASE")
if not URL_DATABASE:
    raise ValueError("Environment variable 'URL_DATABASE' is not set. Please set it in your .env file.")

# print(URL_DATABASE)

engine = create_engine(URL_DATABASE)

# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def connect_db():
    # db = SessionLocal()
    session = Session(engine)        
    try:
        return session
    finally:
        session.close()

DBSession = Annotated[Session, Depends(connect_db)]
# def connect_db():
#     SUPABASE_URL = os.getenv("SUPABASE_URL")
#     SUPABASE_KEY = os.getenv("SUPABASE_KEY")
#     db: Client = create_client(SUPABASE_URL,SUPABASE_KEY)
#     return db

# DBSession = Annotated[Client, Depends(connect_db)]