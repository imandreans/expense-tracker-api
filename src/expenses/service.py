from ..auth.model import TokenData
from supabase import Client
from .model import CreateExpense
from uuid import uuid4
from fastapi import HTTPException
import logging

def create_expenses(db: Client, current_user: TokenData, expense: CreateExpense):
        try:    
                logging.info("Getting user's balance...")  
                user = db.table("Users").select("*").eq("id", current_user.user_id).execute()
                balance = user.data[0]['balance']
                logging.info("Inputting new expense...")
                db.table("Expenses").insert({
                       "id" : str(expense.id),
                       "title" : expense.title,
                       "price" : expense.price,
                       "category" : expense.category.value,
                       "created_at" : str(expense.date),
                       "user_id": current_user.user_id
                }).execute()

                logging.info("Updating user's balance")
                new_balance = int(balance)-expense.price
                db.table("Users").update({"balance": new_balance}).eq('id', current_user.user_id).execute()
                logging.info("Expense is added")
                return {"Status" : 201, "Message" : f"{expense.title} is added"}
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))
 
    

def delete_expense(db: Client, current_user: TokenData, expense_id):
        try:    
                logging.info("Getting user's data")
                user = db.table("Users").select("*").eq("id", current_user.user_id).execute()
                balance = user.data[0]['balance']

                logging.info("Deleting the expense")
                expense_data = get_expense(db, expense_id)
                price = expense_data['price']

                db.table("Users").update({"balance": balance + price}).eq('id', current_user.user_id).execute()
                db.table("Expenses").delete().eq('id', expense_id).execute()
                logging.info("Expense is deleted")
                return {"Status" : 200, "Message" : "Expense is deleted"}
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))
 
def edit_expense(db: Client, current_user: TokenData, expense_id, expense: CreateExpense):
        try:
                logging.info("Getting id and balance user")
                user = db.table("Users").select("id, balance").eq("id", current_user.user_id).execute()
                balance = user.data[0]['balance']

                expense_data = get_expense(db, expense_id)
                user_balance = float(balance)
                current_price = float(expense_data['price'])
                
                user_balance = user_balance if expense.price == current_price else user_balance + current_price - expense.price 
                
                logging.info("Updating user's expense")
                db.table("Expenses").update({"price": expense.price ,
                                                "title": expense.title ,
                                                "category": expense.category ,
                                                "created_at": str(expense.date)}).eq("id", expense_id).execute()

                
                db.table("Users").update({"balance": user_balance}).eq('id', current_user.user_id).execute()
                logging.info("Expense is updated")
                return {"Status" : 200, "Message" : "Expense is edited"}
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))


def list_all_expenses(db: Client, current_user: TokenData):
    try:
        logging.info("Listing expenses...")
        expenses = db.table("Expenses").select("*").eq("user_id", current_user.user_id).execute()
        logging.info("Expenses are listed")
        return expenses.data
    except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))

def get_expense(db: Client, expense_id):
        try:
                logging.info("Getting the expense...")
                expenses = db.table("Expenses").select("*").eq("id", expense_id).execute()
                logging.info("Expense is listed")
                return expenses.data[0]
        except Exception as e:
               logging.error(str(e))
               raise HTTPException(status_code=500, detail=str(e))