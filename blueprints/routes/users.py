from flask import Blueprint
from flask import render_template, url_for, request, redirect, flash, make_response, current_app
from functools import wraps
import jwt

from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import os

from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, DateField, FloatField, PasswordField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

user_bp = Blueprint('user', __name__, template_folder="templates")

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

@user_bp.route('/signup', methods=['POST', 'GET'])
def signup():
    form = SignUpForm()
    conn: Client = current_app.supabase
    bycrypt = current_app.bycrypt
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data

        password = bycrypt.generate_password_hash(form.password.data).decode('utf-8')
        balance  = form.balance.data
        
        user = conn.table("Users").select("*").eq("username", username).execute()

        if len(user.data) == 0:
            conn.table("Users").insert({"username": username,
                                       "password": password,
                                       "balance": balance}).execute()

            return redirect(url_for('login'))
        
        flash('Username already Exist')

    return render_template('signup.html', form=form)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    conn: Client = current_app.supabase
    bycrypt = current_app.bycrypt
    form = LogInForm()
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data
        password = form.password.data
        
        user = conn.table("Users").select("*").eq("username", username).execute()
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

@user_bp.route('/add', methods=['GET', 'POST'])
@token_required
def add_expense():
    conn: Client = current_app.supabase
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
    form = ExpenseForm()
    
    if form.validate_on_submit() and request.method == 'POST':
        price = form.price.data
        description = form.details.data
        category = form.category.data
        date = form.date.data

        user = conn.table("Users").select("*").eq("username", payload['user']).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['id']
        conn.table("Expenses").insert({'user_id': user_id,
                                       "price": price,
                                       "title": description,
                                       "category": category,
                                       "created_at": str(date)}).execute()


        new_balance = int(balance)-price
        print(user_id)
        conn.table("Users").update({"balance": new_balance}).eq('id', user_id).execute()

        # query = """ UPDATE public."Users" SET balance=%(new_balance)s WHERE id =%(id)s """
        # params = {'new_balance':int(new_balance), 'id':user_id}

        # execute_query(query=query, parms=params)

        return redirect(url_for('home'))
    return render_template('add-expense.html', form=form)

@user_bp.route('/delete/<id>')
@token_required
def delete_expense(id):
    conn: Client = current_app.supabase
    token = request.cookies.get('auth_token')
    payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])

    user = conn.table("Users").select("*").eq("username", payload['user']).execute()
    balance = user.data[0]['balance']
    user_id = user.data[0]['id']

    expenses = conn.table("Expenses").select("*").eq('user_id', user_id).eq("id", id).execute()
    print(expenses)
    price = expenses.data[0]['price']

    conn.table("Users").update({"balance": balance + price}).eq('id', user_id).execute()

    conn.table("Expenses").delete().eq('id', id).execute()
        
    return redirect(url_for('home'))

@user_bp.route('/edit/<id>', methods=['GET', 'POST'])
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

    if form.validate_on_submit() and request.method == 'POST':
        
        user = conn.table("Users").select("id, balance").eq("username", payload["user"]).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['id']

        price = float(request.form['price'])
        detail = request.form['details']
        category = request.form['category']
        date = datetime.strptime(request.form['date'], f"%Y-%m-%d")
        
        user_balance = float(balance)
        current_price = float(expense_data['price'])
        
        user_balance = user_balance if price == current_price else user_balance + current_price - price
        
        conn.table("Expenses").update({"price": price,
                                       "title": detail,
                                       "category": category,
                                       "created_at": str(date)}).eq("id", id).execute()

        
        conn.table("Users").update({"balance": user_balance}).eq('id', user_id).execute()

        return redirect(url_for('home'))
    
    return render_template('edit-expense.html', form=form)

@user_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('auth_token', expires=0)
    return response