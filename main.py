from flask import Flask, render_template, url_for, request, redirect, flash, make_response
from functools import wraps
import jwt
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

import os
from os.path import join, dirname
from dotenv import load_dotenv

import psycopg2

from flask_wtf import FlaskForm
from flask_wtf import CSRFProtect

from wtforms import StringField, SubmitField, DateField, FloatField, PasswordField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

csrf = CSRFProtect(app)
bycrypt = Bcrypt(app)
dotenv_path = join(dirname(__file__), '.env')

load_dotenv(dotenv_path)

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
        # except Exception as e:
        #     # error = f'Unknown error has occured - {e}'
        #     return e
    return decorated

def connect_to_db():
    try:
        with app.app_context():
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            supabase: Client = create_client(url,key)
        return supabase
    except Exception as e:
        error = f'Unknown error has occured - {e}'
        return render_template('400.html', error=error)
# def connect_to_db():
#     try:
#         conn = psycopg2.connect(host=os.getenv("HOST"), dbname= os.getenv("DB_NAME"),
#                             user=os.getenv("USER_DB"), password=os.getenv("PASSWORD"),
#                             port=os.getenv("PORT"))
#         return conn
#     except psycopg2.Error as e:
#         return render_template('400.html', error=e)
#     except Exception as e:
#         error = f'Unknown error has occured - {e}'
#         return render_template('400.html', error=error)

def execute_query(query, parms=None):
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, parms)
            conn.commit()
            data = cursor.fetchall()
            conn.close
            return data
    except Exception as e:
        conn.rollback()
        error = f'Unknown error has occured - {e}'
        return render_template('400.html', error=error)

# def execute_query(query, parms=None):
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute(query, parms)
#             conn.commit()
#             data = cursor.fetchall()
#             conn.close
#             return data
#     except psycopg2.Error as e:
#         conn.rollback()
#         return render_template('400.html', error=e)
#     except Exception as e:
#         conn.rollback()
#         error = f'Unknown error has occured - {e}'
#         return render_template('400.html', error=error)

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required as your identity')]) 
    balance = FloatField('Balance', default=0, widget=NumberInput(min=0),validators=[DataRequired(message='Balance is required')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required')])
    submit = SubmitField('Sign Up')

class LogInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required as your identity')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required')])
    submit = SubmitField('Log In')

class ExpenseForm(FlaskForm):

    price = FloatField('Price', default=0, widget=NumberInput(min=0) , validators=[DataRequired(message='Please, Input your the price')])
    details = StringField('Details', validators=[DataRequired(message='Please, Input your info about the expense')])
    category_list = ['Groceries','Leisure', 'Electronics', 'Utilities', 'Clothing', 'Health', 'Others']
    category = SelectField('Category', choices=category_list)
    date = DateField('Date', validators=[DataRequired(message='Please, Input the date')])
    submit_add = SubmitField('Add')
    submit_edit = SubmitField('Edit')     

conn = connect_to_db()

@app.route('/', methods=['GET', 'POST'])
def home():
    token = request.cookies.get('auth_token')
    if token:
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
        
        user = conn.table("User").select("*").eq("username", payload['user']).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['user_id']

        expenses = conn.table("Expenses").select("*").eq("user_id", user_id)

        start_date = request.form['start-date'] if 'start-date' in request.form else ''
        end_date = request.form['end-date'] if 'end-date' in request.form else ''

        if 'filter-date' in request.form:
            selected_filter= request.form['filter-date']
            current_date = datetime.now()
            match selected_filter:
                case 'past-month':
                    past_month = current_date - timedelta(days=30)
                    expenses = expenses.gte("date", past_month)
                case 'past-week':
                    past_week = current_date - timedelta(days=7)
                    expenses = expenses.gte("date", past_week)
                case 'last-three-months':
                    last_three_months = current_date - timedelta(days=90)
                    expenses = expenses.gte("date", last_three_months)

        if len(start_date) > 0:
            expenses = expenses.gte("date", start_date)

        if len(end_date) > 0:
            expenses = expenses.lte("date", end_date)

        selected_date = start_date, end_date
        
        expenses = expenses.execute()
        expenses = expenses.data

        # expenses = execute_query(query=query, parms=params)[::-1]
        
        # query = """ SELECT balance FROM public."User" WHERE username=%(username)s """
        # params = {'username':payload['user']}
        # balance = execute_query(query=query, parms=params)[0][0]

        return render_template('home.html', selected_date=selected_date, user=payload['user'], expenses=expenses, balance=balance)
    return render_template('home.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data

        password = bycrypt.generate_password_hash(form.password.data).decode('utf-8')
        balance  = form.balance.data
        
        # query = """ SELECT username FROM public."User" WHERE username=%(username)s"""
        # params = {'username':username}
        # username_in_db = execute_query(query=query, parms=params)
        
        user = conn.table("User").select("*").eq("username", username).execute()

        if len(user.data) == 0:
            conn.table("User").insert({"username": username,
                                       "password": password,
                                       "balance": balance}).execute()
            # query = """ INSERT INTO public."User" (username, password, balance) VALUES (%(username)s, %(password)s, %(balance)s)"""
            # params = {'username':username, 'password': password, 'balance': balance}
            # execute_query(query=query, parms=params)
            return redirect(url_for('login'))
        
        flash('Username already Exist')

    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data
        password = form.password.data
        
        # query = """ SELECT * FROM public."User" WHERE username = %(username)s"""    
        # params = {'username':username}
        # user = execute_query(query=query, parms=params)
        
        user = conn.table("User").select("*").eq("username", username).execute()


        check_password = bycrypt.check_password_hash(user.data[0]['password'], password)
        
        if user and check_password:
            try:
                exp = datetime.now(timezone.utc) + timedelta(days=1)
                token = jwt.encode({
                        'user' : user.data[0]['username'],
                        'expiration': int(exp.timestamp())
                }, os.getenv('JWT_SECRET_KEY'))
                flash("Log In Success!", "info")
                response = make_response(redirect(url_for('home')))
                response.set_cookie('auth_token',
                                    token,
                                    httponly=True,
                                    secure=True,
                                    samesite='Strict')
                return response
            except Exception as e:
                return render_template('400.html', error=e)
        else:
            flash('username or password isnt valid', 'info')
    return render_template('login.html', form=form)

@app.route('/add', methods=['GET', 'POST'])
@token_required
def add_expense():
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    
    if form.validate_on_submit() and request.method == 'POST':
        price = form.price.data
        description = form.details.data
        category = form.category.data
        date = form.date.data

        # query = """ 
        #             SELECT id, balance 
        #             FROM public."User" 
        #             WHERE username=%(username)s"""
        # params = {'username': payload['user']}

        # user_id, user_balance = execute_query(query=query, parms=params)[0]
        
        # query = """ INSERT INTO public."Expenses" (user_id, description, date, category, price) VALUES (%(user_id)s, %(description)s, %(date)s, %(category)s, %(price)s) """
        # params = {'user_id':user_id, 
        #           'description':details, 
        #           'date':date, 
        #           'category':category, 
        #           'price':price}

        # execute_query(query=query, parms=params)

        user = conn.table("User").select("*").eq("username", payload['user']).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['user_id']
        conn.table("Expenses").insert({"user_id": user_id,
                                       "price": price,
                                       "description": description,
                                       "category": category,
                                       "date": str(date)}).execute()


        new_balance = int(balance)-price
        print(user_id)
        conn.table("User").update({"balance": new_balance}).eq("user_id", user_id).execute()

        # query = """ UPDATE public."User" SET balance=%(new_balance)s WHERE id =%(id)s """
        # params = {'new_balance':int(new_balance), 'id':user_id}

        # execute_query(query=query, parms=params)

        return redirect(url_for('home'))
    return render_template('add-expense.html', form=form)

@app.route('/delete/<id>')
@token_required
def delete_expense(id):
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])

    user = conn.table("User").select("*").eq("username", payload['user']).execute()
    balance = user.data[0]['balance']
    user_id = user.data[0]['user_id']

    expenses = conn.table("Expenses").select("*").eq("user_id", user_id).eq("expense_id", id).execute()
    price = expenses.data[0]['price']

    conn.table("User").update({"balance": balance + price}).eq("user_id", user_id).execute()

    conn.table("Expenses").delete().eq('expense_id', id).execute()
    # query = """ SELECT e.price, u.balance FROM public."User" as u JOIN public."Expenses" as e ON u.id =e.user_id WHERE u.username=%(username)s and e.expense_id = %(expense_id)s"""
    # params = {'username': payload['user'], 'expense_id': id}

    # price_selected_expense, user_balance = execute_query(query,parms=params)[0]

    # query = """UPDATE public."User" SET balance=%(new_balance)s WHERE username=%(username)s"""
    # params = {'new_balance': (user_balance + price_selected_expense), 'username': payload['user']}
    # execute_query(query, parms=params)
    
    # query = """ DELETE FROM public."Expenses" WHERE expense_id=%(expense_id)s"""
    # params = {'expense_id': id}
    # execute_query(query, parms=params)
        
    return redirect(url_for('home'))

@app.route('/edit/<id>', methods=['GET', 'POST'])
@token_required
def edit_expense(id):
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    
    
    # query = """ SELECT * FROM public."Expenses" Where expense_id=%(expense_id)s"""
    # params = {'expense_id' : id}
    # expense_data = execute_query(query, parms=params)[0]
    expenses = conn.table("Expenses").select("*").execute()
    expense_data = expenses.data[0]
    
    form.price.data = expense_data['price']
    form.details.data = expense_data['description']
    form.date.data = datetime.now()
    form.category.data = expense_data['category']

    if form.validate_on_submit() and request.method == 'POST':
        
        user = conn.table("User").select("user_id, balance").eq("username", payload["user"]).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['user_id']

        price = float(request.form['price'])
        detail = request.form['details']
        category = request.form['category']
        date = datetime.strptime(request.form['date'], f"%Y-%m-%d")
        
        user_balance = float(balance)
        current_price = float(expense_data['price'])
        
        user_balance = user_balance if price == current_price else user_balance + current_price - price
        
        conn.table("Expenses").update({"price": price,
                                       "description": detail,
                                       "category": category,
                                       "date": str(date)}).eq("expense_id", id).execute()

        
        conn.table("User").update({"balance": user_balance}).eq("user_id", user_id).execute()

        return redirect(url_for('home'))
    
    return render_template('edit-expense.html', form=form)

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('auth_token', expires=0)
    return response

if __name__ == '__main__':
    app.run()