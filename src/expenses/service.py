from ..auth.model import TokenData
from sqlalchemy.orm import Session

# from supabase import Client
from .model import CreateExpense
from uuid import uuid4
from fastapi import HTTPException
import logging
from sqlalchemy import select, update, delete
from ..entities.core import Expense, User
from sqlalchemy.orm import Session

def create_expenses(db: Session, current_user: TokenData, expense: CreateExpense):
        try:    
                logging.info("Getting user's balance...")  
                query =  select(User).where(User.id == current_user.user_id)
                user = db.scalars(query).first()
                balance = user.balance
                logging.info("Inputting new expense...")
                new_expense = Expense(
                       id=uuid4(),
                       title= expense.title,
                       price = expense.price,
                       category = expense.category,
                       created_at = expense.date,
                       user_id=current_user.user_id
                )
                db.add(new_expense)
                db.commit()
                
                logging.info("Updating user's balance")
                new_balance = int(balance)-expense.price
                query = update(User).where(User.id == current_user.user_id).values(balance=new_balance)
                db.execute(query)
                db.commit()
                logging.info("Expense is Added")
                return {"Status" : 201, "Message" : f"{expense.title} is added"}
                # user = db.table("Users").select("*").eq("id", current_user.user_id).execute()
                # balance = user.data[0]['balance']
                # logging.info("Inputting new expense...")
                # db.table("Expenses").insert({
                #        "id" : str(expense.id),
                #        "title" : expense.title,
                #        "price" : expense.price,
                #        "category" : expense.category.value,
                #        "created_at" : str(expense.date),
                #        "user_id": current_user.user_id
                # }).execute()

                # logging.info("Updating user's balance")
                # new_balance = int(balance)-expense.price
                # db.table("Users").update({"balance": new_balance}).eq('id', current_user.user_id).execute()
                # logging.info("Expense is added")
                # return {"Status" : 201, "Message" : f"{expense.title} is added"}
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))
 
    

def delete_expense(db: Session, current_user: TokenData, expense_id):
        try:    
                logging.info("Getting user's data")
                # user = db.table("Users").select("*").eq("id", current_user.user_id).execute()
               
                query = select(User).where(User.id == current_user.user_id)
                user = db.scalars(query).first()
                balance = user.balance

                logging.info("Deleting the expense")
                expense_data = get_expense(db, expense_id)
                price = expense_data.price
                balance = user.balance

                # db.table("Users").update({"balance": balance + price}).eq('id', current_user.user_id).execute()
                # db.table("Expenses").delete().eq('id', expense_id).execute()
                query = update(User).where(User.id == current_user.user_id).values(balance = balance + price)
                db.execute(query)
                db.commit()

                query = delete(Expense).where(Expense.id == expense_id)
                db.execute(query)
                db.commit()

                logging.info("Expense is deleted")
                return {"Status" : 200, "Message" : "Expense is deleted"}
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))
 
def edit_expense(db: Session, current_user: TokenData, expense_id, expense: CreateExpense):
        try:
                logging.info("Getting id and balance user")

                query = select(User).where(User.id == current_user.user_id)
                user = db.scalars(query).first()
                # user = db.table("Users").select("id, balance").eq("id", current_user.user_id).execute()
                user_balance = user.balance

                current_expense = get_expense(db, expense_id)
                # user_balance = float(balance)
            
                current_price = current_expense.price
                
                user_balance = user_balance if expense.price == current_price else user_balance + current_price - expense.price 
                
                logging.info("Updating user's expense")
                query = update(Expense).where(Expense.id == expense_id).values(price = expense.price, title = expense.title, category = expense.category)
                db.execute(query)
                db.commit()

                # db.table("Expenses").update({"price": expense.price ,
                #                                 "title": expense.title ,
                #                                 "category": expense.category ,
                #                                 "created_at": str(expense.date)}).eq("id", expense_id).execute()

                

                query = update(User).where(User.id == current_user.user_id).values(balance=user_balance)
                db.execute(query)
                db.commit()
                # db.table("Users").update({"balance": user_balance}).eq('id', current_user.user_id).execute()
                logging.info("Expense is updated")
                return {"Status" : 200, "Message" : "Expense is edited"}
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))


def list_all_expenses(db: Session, current_user: TokenData):
    try:
        logging.info("Listing expenses...")
        query = select(Expense).where(Expense.user_id == current_user.user_id)
        # expenses = db.table("Expenses").select("*").eq("user_id", current_user.user_id).execute()
        expenses = db.scalars(query).all()
        logging.info("Expenses are listed")
        yield expenses
    except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))

def get_expense(db: Session, expense_id):
        try:
                logging.info("Getting the expense...")
                # expenses = db.table("Expenses").select("*").eq("id", expense_id).execute()
                query = select(Expense).where(Expense.id == expense_id)
                expense = db.scalars(query).first()
                logging.info("Expense is listed")
                return expense
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))