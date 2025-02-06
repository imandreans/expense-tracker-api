from flask import Flask, render_template, url_for, request, redirect, session, flash, make_response
from functools import wraps
import jwt
from datetime import datetime, timedelta, timezone

import os
from os.path import join, dirname
from dotenv import load_dotenv

import psycopg2

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, FloatField, PasswordField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

app = Flask(__name__)   
app.secret_key = os.getenv("SECRET_KEY")

dotenv_path = join(dirname(__file__), '.env')

load_dotenv(dotenv_path)

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'token' not in session:
            return make_response({'Alert!' : 'Token is missing!'})
        try:
            payload = jwt.decode(session['token'], os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
            return func(*args, **kwargs)
        except jwt.exceptions.InvalidTokenError as e:
            return make_response({'Alert!': f'Token is Invalid! - {e}'})
        except jwt.exceptions.InvalidAlgorithmError as e:
            return make_response({'Alert!': f'Algorithm is not recognized! - {e}'})
        except jwt.exceptions.ExpiredSignatureError as e:
            return make_response({'Alert!': f'Token is Expired! - {e}'})
    return decorated

def connect_to_db():
    try:
        conn = psycopg2.connect(host=os.getenv("HOST"), dbname= os.getenv("DB_NAME"),
                            user=os.getenv("USER_DB"), password=os.getenv("PASSWORD"),
                            port=os.getenv("PORT"))
        return conn
    except psycopg2.Error as err:
        return make_response({'Alert!': err})
    except Exception as e:
        return make_response(f"An unexpected error occured: {e}")

conn = connect_to_db()
def execute_query(query, parms=None):
    try:

        with conn.cursor() as cursor:
            cursor.execute(query, parms)
            conn.commit()
            return cursor.fetchall()
    except psycopg2.Error as err:
        return make_response({'Alert!': err})
    except Exception as e:
        return make_response(f"An unexpected error occured: {e}")

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

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'token' in session:
        payload = jwt.decode(session['token'], os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
        
        query = """ SELECT e.* 
                    FROM public."User" as u 
                    JOIN public."Expenses" as e 
                    ON u.id =e.user_id 
                    WHERE u.username=%(username)s"""

        params = {'username':payload['user']}
        print(request.form)
        start_date = request.form['start-date'] if 'start-date' in request.form else ''
        end_date = request.form['end-date'] if 'end-date' in request.form else ''

        if 'filter-date' in request.form:
            selected_filter= request.form['filter-date']
            current_date = datetime.now()
            match selected_filter:
                case 'past-month':
                    past_month = current_date - timedelta(days=30)
                    query += " AND date >= %(past_month)s"
                    params['past_month'] = past_month
                case 'past-week':
                    past_week = current_date - timedelta(days=7)
                    query += " AND date >= %(past_week)s"
                    params['past_week'] = past_week
                case 'last-three-months':
                    last_three_months = current_date - timedelta(days=90)
                    query += " AND date >= %(last_three_months)s"
                    params['last_three_months'] = last_three_months

        if len(start_date) > 0:
            query += " AND date >= %(start_date)s"
            params['start_date'] = start_date

        if len(end_date) > 0:
            query += " AND date <= %(end_date)s"
            params['end_date'] = end_date
       
        selected_date = start_date, end_date
        # selected_date = start_date, end_date
        expenses = execute_query(query=query, parms=params)[::-1]
        
        query = """ SELECT balance FROM public."User" WHERE username=%(username)s """
        params = {'username':payload['user']}
        balance = execute_query(query=query, parms=params)[0][0]

        return render_template('home.html', selected_date=selected_date,user=payload['user'], expenses=expenses, balance=balance)
    return render_template('home.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data
        password = form.password.data
        balance  = form.balance.data
        # with conn.cursor() as cur:
        #     cur.execute(""" SELECT username FROM public."User" WHERE username=%(username)s""", {'username':username})
        #     if cur.fetchone() == None:
        #         cur.execute(f""" INSERT INTO public."User" (username, password, balance) VALUES ('{username}', '{password}', {balance})""")
        #         conn.commit()
        
        query = """ SELECT username FROM public."User" WHERE username=%(username)s"""
        params = {'username':username}
        username_in_db = execute_query(query=query, parms=params)
        
        if len(username_in_db) == 0:
            query = """ INSERT INTO public."User" (username, password, balance) VALUES (%(username)s, %(password)s, %(balance)s)"""
            params = {'username':username, 'password': password, 'balance': balance}
            execute_query(query=query, parms=params)
            return redirect(url_for('login'))
        
        flash('Username already Exist')

    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data
        password = form.password.data
        
        query = """ SELECT * FROM public."User" WHERE username = %(username)s and password = %(password)s """    
        params = {'username':username, 'password': password,}
        user = execute_query(query=query, parms=params)
        
        if user:
            token = jwt.encode({
                 'user' : user[0][1],
                 'expiration': str(datetime.now(timezone.utc) + timedelta(seconds=120))
            }, os.getenv('JWT_SECRET_KEY'))

            session['token'] = token
            flash("Log In Success!", "info")
            return redirect(url_for('home'))
        else:
            flash('username or password isnt valid', 'info')
            return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic realm: Authentication Failed!'})
    return render_template('login.html', form=form)

@app.route('/add', methods=['GET', 'POST'])
@token_required
def add_expense():
    payload = jwt.decode(session['token'], os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    
    if form.validate_on_submit() and request.method == 'POST':
        price = form.price.data
        details = form.details.data
        category = form.category.data
        date = form.date.data

        query = """ 
                    SELECT id, balance 
                    FROM public."User" 
                    WHERE username=%(username)s"""
        params = {'username': payload['user']}

        user_id, user_balance = execute_query(query=query, parms=params)[0]
        
        query = """ INSERT INTO public."Expenses" (user_id, description, date, category, price) VALUES (%(user_id)s, %(description)s, %(date)s, %(category)s, %(price)s) """
        params = {'user_id':user_id, 
                  'description':details, 
                  'date':date, 
                  'category':category, 
                  'price':price}

        execute_query(query=query, parms=params)

        new_balance = int(user_balance)-price

        query = """ UPDATE public."User" SET balance=%(new_balance)s WHERE id =%(id)s """
        params = {'new_balance':int(new_balance), 'id':user_id}

        execute_query(query=query, parms=params)

        return redirect(url_for('home'))
    return render_template('add-expense.html', form=form)

@app.route('/delete/<id>')
@token_required
def delete_expense(id):
    payload = jwt.decode(session['token'], os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])

    query = """ SELECT e.price, u.balance FROM public."User" as u JOIN public."Expenses" as e ON u.id =e.user_id WHERE u.username=%(username)s and e.expense_id = %(expense_id)s"""
    params = {'username': payload['user'], 'expense_id': id}

    price_selected_expense, user_balance = execute_query(query,parms=params)[0]

    query = """UPDATE public."User" SET balance=%(new_balance)s WHERE username=%(username)s"""
    params = {'new_balance': (user_balance + price_selected_expense), 'username': payload['user']}
    execute_query(query, parms=params)
    
    query = """ DELETE FROM public."Expenses" WHERE expense_id=%(expense_id)s"""
    params = {'expense_id': id}
    execute_query(query, parms=params)
        
    return redirect(url_for('home'))

@app.route('/edit/<id>', methods=['GET', 'POST'])
@token_required
def edit_expense(id):
    payload = jwt.decode(session['token'], os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    
    
    query = """ SELECT * FROM public."Expenses" Where expense_id=%(expense_id)s"""
    params = {'expense_id' : id}
    expense_data = execute_query(query, parms=params)[0]
    
    form.price.data = expense_data[4]
    form.details.data = expense_data[1]
    form.date.data = expense_data[2]
    form.category.data = expense_data[3]

    if form.validate_on_submit() and request.method == 'POST':
        query = """ SELECT id, balance FROM public."User" WHERE username=%(username)s"""
        params = {'username': payload['user']}
        user_id, user_balance = execute_query(query, parms=params)[0]
        
        price = float(request.form['price'])
        detail = request.form['details']
        category = request.form['category']
        date = request.form['date']
        
        user_balance = float(user_balance)
        current_price = float(expense_data[4])
        
        user_balance = user_balance if price == current_price else user_balance + current_price - price
        
        query = """UPDATE public."Expenses" SET description=%(detail)s, date=%(date)s, category=%(category)s, price=%(price)s WHERE expense_id=%(expense_id)s"""
        params = {'detail': detail, 'date': date, 'category': category, 'price': price, 'expense_id': id}
        execute_query(query, parms=params)
        
        query = """UPDATE public."User" SET balance=%(user_balance)s WHERE id = %(user_id)s"""
        params = {'user_balance': user_balance, 'user_id':user_id}
        execute_query(query, parms=params)

        return redirect(url_for('home'))
    
    return render_template('edit-expense.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)