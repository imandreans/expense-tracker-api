from flask import Blueprint, current_app
from flask import render_template, url_for, request, redirect, current_app
from functools import wraps
import jwt

from datetime import datetime
from supabase import Client
import os

from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, DateField, FloatField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput


class ExpenseForm(FlaskForm):

    price = FloatField('Price', default=0, widget=NumberInput(min=0) , validators=[DataRequired(message='Please, Input your the price')])
    details = StringField('Details', validators=[DataRequired(message='Please, Input your info about the expense')])
    category_list = ['Groceries','Leisure', 'Electronics', 'Utilities', 'Clothing', 'Health', 'Others']
    category = SelectField('Category', choices=category_list)
    date = DateField('Date', validators=[DataRequired(message='Please, Input the date')])
    submit_add = SubmitField('Add')
    submit_edit = SubmitField('Edit')     

expense_bp = Blueprint('expense', __name__, template_folder="templates")

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth_token')
        if not token:
            return render_template('400.html', error='Token is Missing!') 
        try:
            payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
            return func(*args, **kwargs)
        except jwt.exceptions.InvalidTokenError as e:
            error = f'Token is Invalid - {e}'
            return render_template('400.html', error=error)
        except jwt.exceptions.InvalidAlgorithmError as e:
            error = f'Algorithm is not recognized - {e}'
            return render_template('400.html', error=error)
        except jwt.exceptions.ExpiredSignatureError as e:
            error = f'Token is Expired! - {e}'
            return render_template('400.html', error=error)
        except Exception as e:
            # error = f'Unknown error has occured - {e}'
            return e
    return decorated

@expense_bp.route('/add', methods=['GET', 'POST'])
@token_required
def add_expense():
    conn: Client = current_app.supabase
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    try:

        if form.validate_on_submit() and request.method == 'POST':
            price = form.price.data
            title = form.details.data
            category = form.category.data
            date = form.date.data

            current_app.logger.info("\x1b[38;20mCreating new expense (%s) with (%s)", title, price)

            user = conn.table("Users").select("*").eq("username", payload['user']).execute()
            balance = user.data[0]['balance']
            user_id = user.data[0]['id']
            conn.table("Expenses").insert({'user_id': user_id,
                                        "price": price,
                                        "title": title,
                                        "category": category,
                                        "created_at": str(date)}).execute()


            new_balance = int(balance)-price
            conn.table("Users").update({"balance": new_balance}).eq('id', user_id).execute()
            current_app.logger.info("\x1b[38;20mExpense for (%s) is created!", title)

            return redirect(url_for('home'))
    except Exception as e:
        current_app.logger.error(f"\x1b[31;20m{e}")
    return render_template('add-expense.html', form=form)

@expense_bp.route('/delete/<id>')
@token_required
def delete_expense(id):
    try:
        conn: Client = current_app.supabase
        token = request.cookies.get('auth_token')
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])

        user = conn.table("Users").select("*").eq("username", payload['user']).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['id']

        expenses = conn.table("Expenses").select("*").eq('user_id', user_id).eq("id", id).execute()
        price = expenses.data[0]['price']

        current_app.logger.info("\x1b[38;20mDeleting expense...")
        conn.table("Users").update({"balance": balance + price}).eq('id', user_id).execute()
        conn.table("Expenses").delete().eq('id', id).execute()
        
        current_app.logger.info("\x1b[38;20mExpense is deleted!")
    except Exception as e:
        current_app.logger.info(e)
    return redirect(url_for('home'))

@expense_bp.route('/edit/<id>', methods=['GET', 'POST'])
@token_required
def edit_expense(id):
    conn: Client = current_app.supabase
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    expenses = conn.table("Expenses").select("*").eq("id", id).execute()
    expense_data = expenses.data[0]
    
    form.price.data = expense_data['price']
    form.details.data = expense_data['title']
    form.date.data = datetime.now()
    form.category.data = expense_data['category']

    try:
        if form.validate_on_submit() and request.method == 'POST':
            user = conn.table("Users").select("id, balance").eq("username", payload["user"]).execute()
            balance = user.data[0]['balance']
            user_id = user.data[0]['id']

            price = float(request.form['price'])
            title = request.form['details']
            category = request.form['category']
            date = datetime.strptime(request.form['date'], f"%Y-%m-%d")
            
            current_app.logger.info("\x1b[38;20mUpdating expense for (%s) !", title)

            user_balance = float(balance)
            current_price = float(expense_data['price'])
            
            user_balance = user_balance if price == current_price else user_balance + current_price - price
            
            conn.table("Expenses").update({"price": price,
                                        "title": title,
                                        "category": category,
                                        "created_at": str(date)}).eq("id", id).execute()

            
            conn.table("Users").update({"balance": user_balance}).eq('id', user_id).execute()
            current_app.logger.info("\x1b[38;20mThe expense (%s) is updated!", title)

            return redirect(url_for('home'))
    except Exception as e:
        current_app.logger.error(e)

    return render_template('edit-expense.html', form=form)
